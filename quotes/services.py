import html
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import transaction
from django.utils.html import strip_tags
from django.utils.text import Truncator
from postmarker.core import PostmarkClient

from .utils import QuotePDFGenerator

# Sample proposal PDF shows ".44c" which looks like truncation; we round
# half-up (".45c"). Kept as one constant so switching is a one-line change.
COST_ROUNDING = ROUND_HALF_UP
CENT = Decimal('0.01')

# Upper limit on the Description column. A long CKEditor field makes a tall
# row, which can force a page break. Raised from 220 because that cut most
# application texts part-way through a sentence.
DESCRIPTION_MAX_CHARS = 400


def format_cost_in_use(cost):
    """Format a per-fill cost the way the proposal PDF shows it:
    under a dollar → '.45c', otherwise → '$1.20'."""
    cost = cost.quantize(CENT, rounding=COST_ROUNDING)
    if cost < Decimal('1'):
        return f'.{int(cost * 100):02d}c'
    return f'${cost:.2f}'


def build_cost_in_use_snapshot(price, dilutions):
    """JSON-serialisable cost-in-use lines for the selected dilution options.

    `dilutions` is an iterable of DilutionVariant. Empty list means the PDF
    omits the 'Cost in use' block for that line. Options whose maths doesn't
    apply (no value or pack volume) fall back to a note-only entry.
    """
    snapshot = []
    for dilution in dilutions:
        app_type = dilution.application_type
        fills = dilution.fills()
        if fills:
            cost = (Decimal(price) / fills).quantize(CENT, rounding=COST_ROUNDING)
            snapshot.append({
                'label': app_type.name,
                'unit_label': app_type.unit_label,
                'fills': str(fills),
                'cost': str(cost),
                'display': f'{app_type.name} {format_cost_in_use(cost)} {app_type.unit_label}',
            })
        elif dilution.note:
            snapshot.append({
                'label': app_type.name,
                'unit_label': app_type.unit_label,
                'fills': None,
                'cost': None,
                'display': f'{app_type.name}: {dilution.note}',
            })
    return snapshot


def snapshot_line_fields(variant):
    """Denormalised product fields frozen onto a QuoteLine.

    The description comes from `application`, the same field the wall chart
    shows. `description` is the fallback when a product has no application text.
    """
    product = variant.product
    source = product.application or product.description or ''
    description = html.unescape(strip_tags(source))
    description = ' '.join(description.split())
    return {
        'product_name': product.name,
        'product_subheading': product.subheading or '',
        'product_code': variant.code or product.productCode or '',
        'description': Truncator(description).chars(DESCRIPTION_MAX_CHARS),
        'row_color': product.wall_chart_color or '',
    }


def create_quote(*, user, company_name, address='', contact_name='', customer=None, lines):
    """Create a quote with snapshotted lines and generate its PDF.

    `lines` is a list of {'variant': ProductVariant, 'price': Decimal,
    'dilutions': [DilutionVariant]} (dilutions optional — the options the
    salesperson selected to show as cost-in-use on that line).
    Single code path shared by the API submit view and the dashboard page.
    """
    from .models import Quote, QuoteLine

    with transaction.atomic():
        quote = Quote.objects.create(
            company_name=company_name,
            address=address,
            contact_name=contact_name,
            customer=customer,
            created_by=user,
        )
        for i, line in enumerate(lines):
            variant = line['variant']
            dilutions = line.get('dilutions', [])
            quote_line = QuoteLine.objects.create(
                quote=quote,
                product_variant=variant,
                price=line['price'],
                sort_order=i,
                cost_in_use=build_cost_in_use_snapshot(line['price'], dilutions),
                **snapshot_line_fields(variant),
            )
            quote_line.dilutions.set(dilutions)

    # Generate PDF outside the transaction so a PDF failure doesn't roll back the quote
    QuotePDFGenerator(quote).generate_and_save()
    quote.refresh_from_db()
    return quote


def send_quote_pdf_email(quote, email_address):
    """Email the proposal PDF via Postmark, generating it first if missing.

    Raises on failure; RuntimeError if the PDF can't be generated.
    """
    if not quote.pdf:
        QuotePDFGenerator(quote).generate_and_save()
        quote.refresh_from_db()
    if not quote.pdf:
        raise RuntimeError('Failed to generate PDF')

    quote.pdf.open('rb')
    pdf_content = quote.pdf.read()
    quote.pdf.close()

    postmark = PostmarkClient(server_token=settings.POSTMARK_SERVER_API_TOKEN)
    email = postmark.emails.Email(
        From='noreply@geller.co.nz',
        To=email_address,
        Subject=f'Product & Cost Proposal {quote.quote_number} — {quote.company_name}',
        HtmlBody=f'''
            <html>
            <body>
                <h2>Product &amp; Cost Proposal</h2>
                <p>Please find attached your proposal:</p>
                <ul>
                    <li><strong>Proposal Number:</strong> {quote.quote_number}</li>
                    <li><strong>Company:</strong> {quote.company_name}</li>
                    <li><strong>Date:</strong> {quote.date.strftime("%Y-%m-%d")}</li>
                </ul>
            </body>
            </html>
        ''',
        TextBody=f'Proposal Number: {quote.quote_number}\nCompany: {quote.company_name}\nDate: {quote.date.strftime("%Y-%m-%d")}',
    )
    email.attach_binary(content=pdf_content, filename=f'proposal-{quote.quote_number}.pdf')
    email.send()


def refresh_line_snapshots(quote):
    """Re-freeze snapshots from current product data (admin edits only)."""
    for line in quote.lines.select_related('product_variant__product').all():
        variant = line.product_variant
        if variant is None:
            continue
        fields = snapshot_line_fields(variant)
        line.product_name = fields['product_name']
        line.product_subheading = fields['product_subheading']
        line.product_code = fields['product_code']
        line.description = fields['description']
        line.row_color = fields['row_color']
        line.cost_in_use = build_cost_in_use_snapshot(
            line.price,
            line.dilutions.select_related('application_type', 'variant__size').all(),
        )
        line.save()
