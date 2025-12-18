import os
import tempfile
from io import BytesIO
from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from PIL import Image as PILImage
import logging

logger = logging.getLogger(__name__)


class ReportPDFGenerator:
    """Generates professional PDF reports with proper styling and image handling"""

    def __init__(self, report):
        self.report = report
        self.font_config = FontConfiguration()

        # Page dimensions for image sizing (in pixels at 96 DPI)
        # Small size for inline images (with questions)
        self.small_portrait_width = 200
        self.small_portrait_height = 150
        self.small_landscape_width = 200
        self.small_landscape_height = 150

        # Large size for media summary images at the end
        self.large_portrait_width = 350
        self.large_portrait_height = 758
        self.large_landscape_width = 758
        self.large_landscape_height = 350

        # Signature-specific size (small)
        self.signature_width = 150
        self.signature_height = 60

    def get_answer_badge_type(self, answer):
        """Determine the badge type/color for an answer based on QuestionOption badge_type or content"""
        # First, check if answer has selected options with explicit badge_type
        selected_options = list(answer.selected_options.all())
        if selected_options:
            # Use the first option's badge_type if it's not 'default'
            for opt in selected_options:
                if hasattr(opt, 'badge_type') and opt.badge_type != 'default':
                    return opt.badge_type

        # Fallback to text-based detection for text answers or when no badge_type is set
        if answer.text_answer:
            text_lower = answer.text_answer.lower()

            # Red - Failures
            if any(keyword in text_lower for keyword in ['fail', 'incorrect', '0 ppm', 'unapproved', 'dirty floors']):
                return 'fail'

            # Green - Pass/OK
            if any(keyword in text_lower for keyword in ['pass', 'good retail practice', 'ok']):
                return 'pass'

            # Orange - Warnings
            if any(keyword in text_lower for keyword in ['needs attention', 'needs descaling', 'reminder', 'issue']):
                return 'warning'

            # Blue - Info/Neutral (Yes, No, N/A)
            if text_lower.strip() in ['yes', 'no', 'n/a']:
                return 'info'

            # Gray - Data fields (PPM, temperature, etc.)
            if any(unit in text_lower for unit in ['ppm', 'degrees', '°c', 'temp']):
                return 'data'

        # Gray - Number answers (like PPM values, temperatures)
        if answer.number_answer is not None:
            return 'data'

        return 'default'

    def generate(self):
        """Generate PDF and return path to temporary file"""
        try:
            # Get template and render HTML
            template = get_template('reports/pdf_template.html')
            context = self._get_context_data()
            html_content = template.render(context)

            # Generate PDF with proper base URL for media files
            # Convert relative MEDIA_URL to absolute path for WeasyPrint
            if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
                base_url = f"file://{settings.MEDIA_ROOT}/"
            else:
                # Fallback to relative URL
                base_url = settings.MEDIA_URL
            html = HTML(string=html_content, base_url=base_url)
            css = self._get_css_styles()

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.pdf',
                delete=False,
                dir=getattr(settings, 'TEMP_DIR', tempfile.gettempdir())
            )

            # Generate PDF with proper styling
            document = html.render(stylesheets=[css], font_config=self.font_config)
            document.write_pdf(temp_file.name)

            temp_file.close()
            return temp_file.name

        except Exception as e:
            logger.error(f"Error generating PDF for report {self.report.document_number}: {str(e)}")
            return None

    def _get_context_data(self):
        """Prepare context data for PDF template"""
        import pytz

        answers_by_section = self.report.get_all_answers_with_images()
        all_images = []
        all_image_fields = []

        # Process images for each answer and collect for media summary
        for section_answers in answers_by_section.values():
            for answer_data in section_answers:
                # Add badge type for styling
                answer_data['badge_type'] = self.get_answer_badge_type(answer_data['answer'])

                # Process signature images separately with smaller dimensions
                if answer_data['answer'].signature_answer:
                    processed_signature = self._process_images([answer_data['answer'].signature_answer], size='signature')
                    if processed_signature:
                        answer_data['processed_signature'] = processed_signature[0]

                if answer_data['images']:
                    # Process images at small size for inline display
                    answer_data['processed_images'] = self._process_images(answer_data['images'], size='small')
                    # Collect raw image fields for later processing at large size
                    all_image_fields.extend(answer_data['images'])

                # Count flagged items per section
                if 'section_flagged_count' not in answer_data:
                    answer_data['section_flagged_count'] = 0

        # Process all collected images at large size for media summary
        if all_image_fields:
            all_images = self._process_images(all_image_fields, size='large')

        # Calculate section-level flagged counts
        section_flagged_counts = {}
        for section_name, section_answers in answers_by_section.items():
            flagged_in_section = sum(1 for ad in section_answers if ad['badge_type'] in ['fail', 'warning'])
            section_flagged_counts[section_name] = flagged_in_section

        # Get logos
        # Geller company logo (always shown)
        geller_logo = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'reports/static/reports/img/report-logo.png')
        if not os.path.exists(geller_logo):
            # Fallback to STATIC_ROOT path
            geller_logo = os.path.join(settings.STATIC_ROOT or '', 'reports/img/report-logo.png')

        customer_logo = None
        distributor_logo = None

        if self.report.customer and hasattr(self.report.customer, 'primaryImageLink') and self.report.customer.primaryImageLink:
            customer_logo = self.report.customer.primaryImageLink.url

        if self.report.distributor and self.report.distributor.primaryImageLink:
            distributor_logo = self.report.distributor.primaryImageLink.url

        # Get flagged items and statistics
        flagged_statistics = self.report.get_flagged_statistics()
        flagged_answers = self.report.get_flagged_answers()

        # Format timestamp in New Zealand time
        nz_tz = pytz.timezone('Pacific/Auckland')
        generated_at_nz = timezone.now().astimezone(nz_tz)

        return {
            'report': self.report,
            'answers_by_section': answers_by_section,
            'section_flagged_counts': section_flagged_counts,
            'geller_logo': f"file://{geller_logo}" if os.path.exists(geller_logo) else None,
            'customer_logo': customer_logo,
            'distributor_logo': distributor_logo,
            'generated_at': generated_at_nz,
            'company_name': 'Geller & Co',
            'company_website': 'geller.co.nz',
            'flagged_statistics': flagged_statistics,
            'flagged_answers': flagged_answers,
            'all_images': all_images,
        }

    def _process_images(self, images, size='small'):
        """Process images to ensure they meet size requirements

        Args:
            images: List of image fields to process
            size: 'small' for inline images (default), 'large' for media summary, 'signature' for signatures
        """
        processed_images = []

        for image_field in images:
            if not image_field:
                continue

            try:
                # Get image path and URL
                if hasattr(image_field, 'path') and os.path.exists(image_field.path):
                    image_path = image_field.path
                    # Use file:// URL for local files
                    image_url = f"file://{image_field.path}" if hasattr(image_field, 'path') else getattr(image_field, 'url', '')
                elif hasattr(image_field, 'url'):
                    # For images served via URL, convert to file path if possible
                    image_url = image_field.url
                    # Try to convert URL to local file path
                    if settings.MEDIA_URL in image_url and hasattr(settings, 'MEDIA_ROOT'):
                        relative_path = image_url.replace(settings.MEDIA_URL, '')
                        potential_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                        if os.path.exists(potential_path):
                            image_path = potential_path
                            image_url = f"file://{potential_path}"
                        else:
                            # Use original URL as fallback
                            width, height = self._get_default_dimensions(size, True)
                            processed_images.append({
                                'url': image_url,
                                'is_portrait': True,  # Default assumption
                                'width': width,
                                'height': height
                            })
                            continue
                    else:
                        width, height = self._get_default_dimensions(size, True)
                        processed_images.append({
                            'url': image_url,
                            'is_portrait': True,  # Default assumption
                            'width': width,
                            'height': height
                        })
                        continue
                else:
                    continue

                # Open and analyze image
                with PILImage.open(image_path) as img:
                    original_width, original_height = img.size
                    is_portrait = original_height >= original_width

                    # Determine target dimensions based on size parameter
                    max_width, max_height = self._get_max_dimensions(size, is_portrait)

                    # Calculate scaling to fit within constraints
                    width_ratio = max_width / original_width
                    height_ratio = max_height / original_height
                    scale_ratio = min(width_ratio, height_ratio)

                    final_width = int(original_width * scale_ratio)
                    final_height = int(original_height * scale_ratio)

                    processed_images.append({
                        'url': image_url,
                        'is_portrait': is_portrait,
                        'width': final_width,
                        'height': final_height,
                        'original_width': original_width,
                        'original_height': original_height
                    })

            except Exception as e:
                logger.warning(f"Error processing image {image_field}: {str(e)}")
                # Add image anyway with default dimensions, using file:// URL if possible
                fallback_url = getattr(image_field, 'url', '')
                if hasattr(image_field, 'path') and os.path.exists(image_field.path):
                    fallback_url = f"file://{image_field.path}"
                elif settings.MEDIA_URL in fallback_url and hasattr(settings, 'MEDIA_ROOT'):
                    relative_path = fallback_url.replace(settings.MEDIA_URL, '')
                    potential_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                    if os.path.exists(potential_path):
                        fallback_url = f"file://{potential_path}"

                width, height = self._get_default_dimensions(size, True)
                processed_images.append({
                    'url': fallback_url,
                    'is_portrait': True,
                    'width': width,
                    'height': height
                })

        return processed_images

    def _get_max_dimensions(self, size, is_portrait):
        """Get maximum dimensions based on size type and orientation"""
        if size == 'signature':
            return self.signature_width, self.signature_height
        elif size == 'large':
            if is_portrait:
                return self.large_portrait_width, self.large_portrait_height
            else:
                return self.large_landscape_width, self.large_landscape_height
        else:  # small
            if is_portrait:
                return self.small_portrait_width, self.small_portrait_height
            else:
                return self.small_landscape_width, self.small_landscape_height

    def _get_default_dimensions(self, size, is_portrait):
        """Get default dimensions for fallback cases"""
        if size == 'signature':
            return (self.signature_width, self.signature_height)
        elif size == 'large':
            return (self.large_portrait_width, self.large_portrait_height) if is_portrait else (self.large_landscape_width, self.large_landscape_height)
        else:  # small
            return (self.small_portrait_width, self.small_portrait_height) if is_portrait else (self.small_landscape_width, self.small_landscape_height)

    def _get_css_styles(self):
        """Get CSS styles for professional PDF formatting"""
        css_content = """
        @page {
            size: A4 portrait;
            margin: 1.5cm 1.5cm 2.5cm 1.5cm;
            @bottom-left {
                content: "Private & confidential";
                font-family: Arial, sans-serif;
                font-size: 9px;
                color: #666;
            }
            @bottom-right {
                content: counter(page) "/" counter(pages);
                font-family: Arial, sans-serif;
                font-size: 9px;
                color: #666;
            }
        }

        body {
            font-family: Arial, sans-serif;
            font-size: 10px;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
            orphans: 3;
            widows: 3;
        }

        /* Badge Styles - Color coded answer indicators */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 500;
            color: white;
            text-align: center;
        }

        .badge-fail {
            background-color: #dc3545;
            color: white;
        }

        .badge-pass {
            background-color: #28a745;
            color: white;
        }

        .badge-warning {
            background-color: #ff8c00;
            color: white;
        }

        .badge-info {
            background-color: #6c757d;
            color: white;
        }

        .badge-data {
            background-color: #6c757d;
            color: white;
        }

        .badge-complete {
            background-color: #0d6efd;
            color: white;
            padding: 6px 16px;
            font-size: 12px;
        }

        /* Cover Page Styles */
        .cover-header {
            margin-bottom: 30px;
        }

        .logo-section {
            text-align: left;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .geller-logo {
            max-height: 60px;
            max-width: 220px;
        }

        .customer-logo {
            max-height: 50px;
            max-width: 150px;
        }

        .logo {
            max-height: 70px;
            max-width: 200px;
        }

        .report-title-main {
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin: 30px 0 10px 0;
        }

        .report-subtitle {
            font-size: 13px;
            color: #666;
            margin: 0 0 20px 0;
        }

        .status-badge-line {
            text-align: right;
            margin-bottom: 20px;
        }

        /* Summary Statistics Box */
        .summary-stats {
            display: flex;
            justify-content: space-between;
            background-color: #e9ecef;
            padding: 12px 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }

        .stat-item {
            display: flex;
            align-items: center;
        }

        .stat-label {
            font-weight: bold;
            margin-right: 10px;
            color: #333;
        }

        .stat-value {
            font-size: 14px;
            font-weight: bold;
            color: #333;
        }

        /* Metadata Table */
        .metadata-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            font-size: 11px;
        }

        .metadata-table tr {
            border-bottom: 1px solid #dee2e6;
        }

        .metadata-table td {
            padding: 10px 15px;
            vertical-align: top;
        }

        .metadata-table .label {
            font-weight: bold;
            color: #333;
            width: 35%;
            background-color: #f8f9fa;
        }

        .metadata-table .value {
            color: #666;
            background-color: white;
        }

        .metadata-table .value-highlight {
            background-color: #6c757d;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
        }

        /* Flagged Items Page */
        .flagged-items-page {
            page-break-before: always;
            margin-bottom: 30px;
        }

        .flagged-title {
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin: 0 0 5px 0;
            padding: 10px 0;
        }

        .flagged-count {
            font-size: 11px;
            color: #666;
            margin-bottom: 20px;
        }

        .flagged-item {
            margin-bottom: 20px;
            padding: 12px;
            border-left: 4px solid #dc3545;
            background-color: #f8f9fa;
            page-break-inside: avoid;
        }

        .flagged-item-header {
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
            font-size: 11px;
        }

        .flagged-item-question {
            color: #666;
            margin-bottom: 8px;
            font-size: 10px;
        }

        .flagged-item-answer {
            margin-bottom: 10px;
        }

        .flagged-notes {
            background-color: white;
            padding: 8px;
            margin-top: 10px;
            border-radius: 3px;
            font-size: 9px;
        }

        /* Section Styles */
        .section {
            margin-bottom: 30px;
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            page-break-after: avoid;
        }

        .section-title {
            font-size: 13px;
            font-weight: bold;
            color: #333;
            margin: 0;
            padding: 8px 12px;
            background-color: #e9ecef;
            flex-grow: 1;
        }

        .section-flagged-badge {
            background-color: #dc3545;
            color: white;
            padding: 4px 10px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 10px;
        }

        .question-block {
            margin-bottom: 18px;
            page-break-inside: avoid;
            orphans: 2;
            widows: 2;
        }

        .question {
            font-weight: bold;
            color: #333;
            margin-bottom: 6px;
            line-height: 1.3;
            font-size: 10px;
        }

        .answer-row {
            display: flex;
            align-items: flex-start;
            margin-bottom: 10px;
        }

        .answer-label {
            min-width: 200px;
            font-weight: normal;
            color: #666;
            font-size: 10px;
        }

        .answer-value {
            flex-grow: 1;
        }

        /* Signature Styles */
        .signature-section {
            margin-top: 15px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 3px;
            page-break-inside: avoid;
        }

        .signature-label {
            font-weight: bold;
            font-size: 10px;
            margin-bottom: 8px;
        }

        .signature-image {
            max-width: 150px;
            max-height: 60px;
            border: 1px solid #dee2e6;
            background-color: white;
            padding: 5px;
        }

        .signature-info {
            margin-top: 5px;
            font-size: 9px;
            color: #666;
        }

        /* Image Styles */
        .image-container {
            margin: 15px 0;
            text-align: center;
            page-break-inside: avoid;
            page-break-before: auto;
            page-break-after: auto;
        }

        .report-image {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 3px;
        }

        .image-caption {
            font-size: 8px;
            color: #666;
            margin-top: 5px;
        }

        /* Media Summary Page */
        .media-summary-page {
            page-break-before: always;
        }

        .media-title {
            font-size: 14px;
            font-weight: bold;
            color: #333;
            margin: 0 0 20px 0;
            padding: 10px 12px;
            background-color: #e9ecef;
        }

        .media-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .media-item {
            text-align: center;
            page-break-inside: avoid;
        }

        .media-item img {
            max-width: 100%;
            max-height: 250px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }

        .media-item-caption {
            font-size: 9px;
            color: #333;
            margin-top: 8px;
            font-weight: 500;
        }

        /* Page break handling */
        .page-break {
            page-break-before: always;
        }

        /* Ensure images don't break across pages */
        .question-block img,
        .image-container {
            page-break-inside: avoid;
        }

        /* Notes and comments */
        .notes-section {
            margin-top: 10px;
            padding: 8px;
            background-color: #fff3cd;
            border-left: 3px solid #ffc107;
            font-size: 9px;
            page-break-inside: avoid;
        }

        .notes-label {
            font-weight: bold;
            color: #856404;
            margin-bottom: 5px;
        }

        /* PDF attachments */
        .pdf-attachment {
            margin-top: 10px;
            padding: 8px;
            background-color: #e7f3ff;
            border-radius: 3px;
            font-size: 9px;
        }

        .pdf-link {
            color: #0066cc;
            text-decoration: underline;
        }

        /* Miscellaneous */
        .required-marker {
            color: #dc3545;
            font-weight: bold;
        }

        .no-answer {
            color: #999;
            font-style: italic;
        }

        strong {
            font-weight: 600;
        }

        em {
            font-style: italic;
        }
        """

        return CSS(string=css_content, font_config=self.font_config)