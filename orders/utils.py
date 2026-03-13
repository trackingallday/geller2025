import os
import tempfile
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import get_template
from django.utils import timezone
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

logger = logging.getLogger(__name__)


class OrderPDFGenerator:
    """Generates a branded PDF for a CustomerOrder using WeasyPrint."""

    def __init__(self, order):
        self.order = order
        self.font_config = FontConfiguration()

    def generate_and_save(self):
        """Render HTML → WeasyPrint PDF → save to order.pdf without re-triggering the signal."""
        try:
            template = get_template('orders/pdf_template.html')
            context = self._get_context()
            html_content = template.render(context)

            css = self._get_css()
            html = HTML(string=html_content, base_url=f"file://{settings.BASE_DIR}/")
            document = html.render(stylesheets=[css], font_config=self.font_config)

            pdf_bytes = document.write_pdf()

            filename = f'order_{self.order.order_number}.pdf'

            # Use .update() to avoid re-triggering the post_save signal
            from .models import CustomerOrder
            from django.core.files.storage import default_storage

            # Save file via storage
            file_path = f'order_pdfs/{filename}'
            saved_path = default_storage.save(file_path, ContentFile(pdf_bytes))

            CustomerOrder.objects.filter(pk=self.order.pk).update(pdf=saved_path)

        except Exception as e:
            logger.error(f"Error generating PDF for order {self.order.order_number}: {e}")

    def _get_context(self):
        import pytz

        geller_logo = os.path.join(
            settings.BASE_DIR, 'reports', 'static', 'reports', 'img', 'report-logo.png'
        )

        nz_tz = pytz.timezone('Pacific/Auckland')
        generated_at = timezone.now().astimezone(nz_tz)

        return {
            'order': self.order,
            'line_items': self.order.line_items.select_related('product_variant__product', 'product_variant__size').all(),
            'geller_logo': f"file://{geller_logo}" if os.path.exists(geller_logo) else None,
            'generated_at': generated_at,
            'company_name': 'Geller & Co',
            'company_website': 'geller.co.nz',
        }

    def _get_css(self):
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
        }

        .logo-section {
            margin-bottom: 20px;
        }

        .geller-logo {
            max-height: 60px;
            max-width: 220px;
        }

        .order-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin: 20px 0 5px 0;
        }

        .order-number {
            font-size: 13px;
            color: #666;
            margin-bottom: 20px;
        }

        .metadata-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            font-size: 11px;
        }

        .metadata-table tr {
            border-bottom: 1px solid #dee2e6;
        }

        .metadata-table td {
            padding: 8px 12px;
            vertical-align: top;
        }

        .metadata-table .label {
            font-weight: bold;
            color: #333;
            width: 35%;
            background-color: #f8f9fa;
        }

        .metadata-table .value {
            color: #555;
            background-color: white;
        }

        .status-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            color: white;
        }

        .status-pending    { background-color: #6c757d; }
        .status-processing { background-color: #0d6efd; }
        .status-fulfilled  { background-color: #28a745; }
        .status-cancelled  { background-color: #dc3545; }

        .section-title {
            font-size: 13px;
            font-weight: bold;
            color: #333;
            padding: 8px 12px;
            background-color: #e9ecef;
            margin: 0 0 10px 0;
        }

        .line-items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            font-size: 11px;
        }

        .line-items-table th {
            background-color: #343a40;
            color: white;
            padding: 8px 12px;
            text-align: left;
            font-weight: bold;
        }

        .line-items-table td {
            padding: 8px 12px;
            border-bottom: 1px solid #dee2e6;
            vertical-align: top;
        }

        .line-items-table tr:nth-child(even) td {
            background-color: #f8f9fa;
        }

        .notes-section {
            margin-top: 10px;
            padding: 10px 12px;
            background-color: #fff3cd;
            border-left: 3px solid #ffc107;
            font-size: 10px;
        }

        .notes-label {
            font-weight: bold;
            color: #856404;
            margin-bottom: 5px;
        }
        """
        return CSS(string=css_content, font_config=self.font_config)
