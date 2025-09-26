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
        self.portrait_width = 600
        self.portrait_height = 900
        self.landscape_width = 900
        self.landscape_height = 600

    def generate(self):
        """Generate PDF and return path to temporary file"""
        try:
            # Get template and render HTML
            template = get_template('reports/pdf_template.html')
            context = self._get_context_data()
            html_content = template.render(context)

            # Generate PDF
            html = HTML(string=html_content, base_url=settings.MEDIA_URL)
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
        answers_by_section = self.report.get_all_answers_with_images()

        # Process images for each answer
        for section_answers in answers_by_section.values():
            for answer_data in section_answers:
                if answer_data['images']:
                    answer_data['processed_images'] = self._process_images(answer_data['images'])

        # Get logos
        customer_logo = None
        distributor_logo = None

        if self.report.customer and hasattr(self.report.customer, 'primaryImageLink') and self.report.customer.primaryImageLink:
            customer_logo = self.report.customer.primaryImageLink.url

        if self.report.distributor and self.report.distributor.primaryImageLink:
            distributor_logo = self.report.distributor.primaryImageLink.url

        return {
            'report': self.report,
            'answers_by_section': answers_by_section,
            'customer_logo': customer_logo,
            'distributor_logo': distributor_logo,
            'generated_at': timezone.now(),
            'company_name': 'Geller & Co',
            'company_website': 'geller.co.nz',
        }

    def _process_images(self, images):
        """Process images to ensure they meet size requirements"""
        processed_images = []

        for image_field in images:
            if not image_field:
                continue

            try:
                # Get image path
                if hasattr(image_field, 'path') and os.path.exists(image_field.path):
                    image_path = image_field.path
                elif hasattr(image_field, 'url'):
                    # For images served via URL, we'll use the URL directly
                    processed_images.append({
                        'url': image_field.url,
                        'is_portrait': True,  # Default assumption
                        'width': self.portrait_width,
                        'height': self.portrait_height
                    })
                    continue
                else:
                    continue

                # Open and analyze image
                with PILImage.open(image_path) as img:
                    original_width, original_height = img.size
                    is_portrait = original_height >= original_width

                    # Determine target dimensions
                    if is_portrait:
                        max_width = self.portrait_width
                        max_height = self.portrait_height
                    else:
                        max_width = self.landscape_width
                        max_height = self.landscape_height

                    # Calculate scaling to fit within constraints
                    width_ratio = max_width / original_width
                    height_ratio = max_height / original_height
                    scale_ratio = min(width_ratio, height_ratio)

                    final_width = int(original_width * scale_ratio)
                    final_height = int(original_height * scale_ratio)

                    processed_images.append({
                        'url': image_field.url,
                        'is_portrait': is_portrait,
                        'width': final_width,
                        'height': final_height,
                        'original_width': original_width,
                        'original_height': original_height
                    })

            except Exception as e:
                logger.warning(f"Error processing image {image_field}: {str(e)}")
                # Add image anyway with default dimensions
                processed_images.append({
                    'url': getattr(image_field, 'url', ''),
                    'is_portrait': True,
                    'width': self.portrait_width,
                    'height': self.portrait_height
                })

        return processed_images

    def _get_css_styles(self):
        """Get CSS styles for professional PDF formatting"""
        css_content = """
        @page {
            size: A4 portrait;
            margin: 2cm 1.5cm 2cm 1.5cm;
            @bottom-center {
                content: "geller.co.nz";
                font-family: Arial, sans-serif;
                font-size: 10px;
                color: #666;
            }
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
                font-family: Arial, sans-serif;
                font-size: 10px;
                color: #666;
            }
        }

        body {
            font-family: Arial, sans-serif;
            font-size: 11px;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid #0066cc;
        }

        .header-left {
            flex: 1;
        }

        .header-right {
            flex: 0 0 auto;
            text-align: right;
        }

        .logo {
            max-height: 60px;
            max-width: 150px;
            margin-bottom: 10px;
        }

        .company-info {
            font-size: 10px;
            color: #666;
            margin-top: 5px;
        }

        .report-title {
            font-size: 18px;
            font-weight: bold;
            color: #0066cc;
            margin: 0 0 10px 0;
        }

        .report-meta {
            font-size: 12px;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 25px;
        }

        .report-meta table {
            width: 100%;
            border-collapse: collapse;
        }

        .report-meta td {
            padding: 5px;
            border: none;
        }

        .report-meta .label {
            font-weight: bold;
            color: #555;
            width: 30%;
        }

        .section {
            margin-bottom: 30px;
            page-break-inside: avoid;
        }

        .section-title {
            font-size: 14px;
            font-weight: bold;
            color: #0066cc;
            margin: 0 0 15px 0;
            padding: 8px 12px;
            background-color: #e6f2ff;
            border-left: 4px solid #0066cc;
        }

        .question-block {
            margin-bottom: 20px;
            page-break-inside: avoid;
        }

        .question {
            font-weight: bold;
            color: #444;
            margin-bottom: 8px;
            line-height: 1.3;
        }

        .answer {
            background-color: #f8f9fa;
            padding: 10px;
            border-left: 3px solid #28a745;
            margin-bottom: 10px;
        }

        .answer-text {
            font-size: 11px;
            line-height: 1.4;
        }

        .image-container {
            margin: 15px 0;
            text-align: center;
            page-break-inside: avoid;
        }

        .report-image {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .image-caption {
            font-size: 9px;
            color: #666;
            margin-top: 5px;
            font-style: italic;
        }

        .footer-info {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 10px;
            color: #666;
            text-align: center;
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

        /* Status styling */
        .status-draft { color: #856404; }
        .status-submitted { color: #0066cc; }
        .status-approved { color: #28a745; }
        .status-rejected { color: #dc3545; }

        /* Responsive image handling */
        @media print {
            .report-image {
                max-height: 400px;
            }
        }
        """

        return CSS(string=css_content, font_config=self.font_config)