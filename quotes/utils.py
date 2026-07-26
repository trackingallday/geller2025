import logging
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import get_template
from django.utils import timezone
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

logger = logging.getLogger(__name__)

GELLER_PURPLE = '#5A2D82'
ROW_TINT_GREY = '#ECEDEF'
ROW_TINT_CREAM = '#FBF3D9'


class QuotePDFGenerator:
    """Generates a branded 'Product & Cost Proposal' PDF for a Quote using WeasyPrint."""

    def __init__(self, quote):
        self.quote = quote
        self.font_config = FontConfiguration()

    def generate_and_save(self):
        """Render HTML → WeasyPrint PDF → save to quote.pdf without re-triggering save()."""
        try:
            template = get_template('quotes/pdf_template.html')
            context = self._get_context()
            html_content = template.render(context)

            css = self._get_css()
            html = HTML(string=html_content, base_url=f"file://{settings.BASE_DIR}/")
            document = html.render(stylesheets=[css], font_config=self.font_config)

            pdf_bytes = document.write_pdf()

            from django.core.files.storage import default_storage
            from .models import Quote

            file_path = f'quote_pdfs/quote_{self.quote.quote_number}.pdf'
            saved_path = default_storage.save(file_path, ContentFile(pdf_bytes))

            # .update() avoids re-triggering Quote.save()
            Quote.objects.filter(pk=self.quote.pk).update(pdf=saved_path)

        except Exception as e:
            logger.error(f"Error generating PDF for quote {self.quote.quote_number}: {e}")

    def _image_path(self, line):
        """file:// path to the line's image: variant image, else product primary image."""
        variant = line.product_variant
        if variant is None:
            return None
        for field in (variant.image, variant.product.primaryImageLink):
            if field:
                try:
                    path = field.path
                except (ValueError, NotImplementedError):
                    continue
                if os.path.exists(path):
                    return f'file://{path}'
        return None

    def _get_context(self):
        import pytz

        nz_tz = pytz.timezone('Pacific/Auckland')

        lines = []
        for line in self.quote.lines.select_related('product_variant__product').all():
            lines.append({
                'line': line,
                'image_src': self._image_path(line),
            })

        return {
            'quote': self.quote,
            'lines': lines,
            'quote_date': self.quote.date.astimezone(nz_tz),
            'company_website': 'geller.co.nz',
        }

    def _get_css(self):
        css_content = """
        @page {
            size: A4 portrait;
            margin: 0 0 1.8cm 0;
            @bottom-center {
                content: element(footer);
                width: 100%%;
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

        /* Header */
        .header-bar {
            background-color: %(purple)s;
            color: white;
            padding: 26px 34px;
        }

        .header-table { width: 100%%; border-collapse: collapse; }
        .header-table td { vertical-align: middle; }

        .header-title {
            font-size: 26px;
            font-weight: bold;
        }
        .header-title .light { font-weight: normal; }

        .wordmark {
            text-align: right;
            font-size: 34px;
            font-weight: bold;
            line-height: 1;
        }
        .wordmark .reg { font-size: 12px; vertical-align: super; }
        .tagline {
            text-align: right;
            font-size: 9px;
            border-top: 1px solid rgba(255,255,255,0.6);
            padding-top: 3px;
            margin-top: 4px;
        }
        .wordmark-block { display: inline-block; text-align: right; }
        .header-logo { max-height: 46px; }

        /* Proposal info */
        .info-section {
            padding: 24px 34px 12px 34px;
        }
        .info-table { width: 100%%; border-collapse: collapse; }
        .info-table td { vertical-align: top; }

        .proposal-for-label { font-weight: bold; font-size: 12px; }
        .proposal-for {
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .proposal-att { font-size: 12px; font-weight: bold; margin-top: 4px; }

        .meta-right { text-align: left; font-size: 12px; width: 30%%; }
        .meta-right .meta-row { margin-bottom: 12px; font-weight: bold; }
        .meta-right .meta-value { font-weight: normal; }

        /* Line items */
        .items-section { padding: 6px 34px 0 34px; }

        .items-table { width: 100%%; border-collapse: collapse; }

        .items-table th {
            font-size: 10px;
            font-weight: bold;
            color: #333;
            text-align: left;
            padding: 6px 8px;
            border-bottom: 1.5px solid #333;
        }

        .items-table td {
            padding: 12px 8px;
            vertical-align: top;
        }

        .row-grey td { background-color: %(grey)s; }
        .row-cream td { background-color: %(cream)s; }

        /* Image fills the whole cell (row height included) via background cover */
        .img-cell {
            width: 72px;
            background-color: white !important;
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }

        .product-cell { width: 22%%; border-left: 6px solid %(purple)s; }
        .row-cream .product-cell { border-left-color: #C9A227; }

        .product-name { font-weight: bold; font-size: 12px; color: #333; }
        .product-subheading { color: #777; font-size: 9px; margin-top: 3px; }

        .code-cell { width: 14%%; font-weight: bold; font-size: 10px; }
        .desc-cell { width: 30%%; font-size: 9.5px; }

        .price-cell { width: 20%%; }
        .price { font-weight: bold; font-size: 12px; }
        .ciu-heading { text-decoration: underline; font-weight: bold; margin: 8px 0 4px 0; }
        .ciu-line { font-weight: bold; }

        /* Footer */
        .footer-bar {
            position: running(footer);
            background-color: %(purple)s;
            color: white;
            font-weight: bold;
            font-size: 11px;
            padding: 12px 34px;
            width: 100%%;
            box-sizing: border-box;
        }
        """ % {'purple': GELLER_PURPLE, 'grey': ROW_TINT_GREY, 'cream': ROW_TINT_CREAM}
        return CSS(string=css_content, font_config=self.font_config)
