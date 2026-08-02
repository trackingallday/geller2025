from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from chemsapp.models import Customer, ProductVariant
from .models import Quote
from .services import create_quote, send_quote_pdf_email


@login_required
def quote_dashboard(request):
    """Admin-facing test page: list of quotes + detail panel (like /tickets/dashboard/)."""
    active_quote_id = request.GET.get('quote', '')

    quotes = (
        Quote.objects
        .select_related('customer', 'created_by')
        .prefetch_related('lines')
        .order_by('-created_at')
    )

    active_quote = None
    if active_quote_id:
        try:
            active_quote = (
                Quote.objects
                .select_related('customer', 'created_by')
                .prefetch_related('lines__product_variant__product')
                .get(pk=active_quote_id)
            )
        except Quote.DoesNotExist:
            pass

    context = {
        'quotes': quotes,
        'active_quote': active_quote,
    }
    return TemplateResponse(request, 'quotes/dashboard.html', context)


def _builder_context():
    variants = ProductVariant.objects.select_related('product', 'size').prefetch_related(
        'dilutions__application_type',
    ).order_by('product__name', 'code')

    catalogue = []
    for v in variants:
        label = v.product.name
        if v.size:
            label += f' — {v.size.name}'
        if v.code:
            label += f' ({v.code})'
        dilution_options = []
        for dilution in v.dilutions.all():
            fills = dilution.fills()
            if fills:
                dilution_options.append({'name': dilution.application_type.name, 'fills': str(fills)})
        catalogue.append({
            'id': v.pk,
            'label': label,
            'dilution_options': dilution_options,
        })

    customers = []
    for c in Customer.objects.prefetch_related('contacts').order_by('businessName'):
        customers.append({
            'id': c.pk,
            'name': c.businessName,
            'address': c.address or '',
            'contacts': [contact.name for contact in c.contacts.all()],
        })

    return {
        'catalogue': catalogue,
        'customers': customers,
    }


@login_required
def dashboard_create_quote(request):
    """Quote builder page: header fields + dynamic product/price lines."""
    error = None

    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        address = request.POST.get('address', '').strip()
        contact_name = request.POST.get('contact_name', '').strip()
        customer_id = request.POST.get('customer_id', '').strip()

        variant_ids = request.POST.getlist('variant_id')
        prices = request.POST.getlist('price')

        lines = []
        for vid, price in zip(variant_ids, prices):
            vid = vid.strip()
            price = price.strip()
            if not vid and not price:
                continue  # skip fully empty rows
            try:
                variant = ProductVariant.objects.select_related('product', 'size').get(pk=vid)
                price_dec = Decimal(price)
                if price_dec <= 0:
                    raise InvalidOperation
            except (ProductVariant.DoesNotExist, InvalidOperation, ValueError):
                lines = None
                error = 'Every line needs a product and a price greater than zero.'
                break
            # Test page has no per-option picker: include all of the variant's dilutions
            lines.append({
                'variant': variant,
                'price': price_dec,
                'dilutions': list(variant.dilutions.select_related('application_type').all()),
            })

        if lines is not None:
            if not company_name:
                error = 'Company name is required.'
            elif not lines:
                error = 'Add at least one product line.'
            else:
                customer = Customer.objects.filter(pk=customer_id).first() if customer_id else None
                quote = create_quote(
                    user=request.user,
                    company_name=company_name,
                    address=address,
                    contact_name=contact_name,
                    customer=customer,
                    lines=lines,
                )
                messages.success(request, f'Proposal {quote.quote_number} created.')
                return redirect(f'/quotes/dashboard/?quote={quote.pk}')

    context = _builder_context()
    context['error'] = error
    context['form_data'] = request.POST if request.method == 'POST' else {}
    return TemplateResponse(request, 'quotes/create.html', context)


@login_required
def dashboard_email_quote(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    if request.method == 'POST':
        email_address = request.POST.get('email_address', '').strip()
        if not email_address:
            messages.error(request, 'Email address is required.')
        else:
            try:
                send_quote_pdf_email(quote, email_address)
                messages.success(request, f'Proposal PDF sent to {email_address}.')
            except Exception as e:
                messages.error(request, f'Failed to send: {e}')
    return redirect(f'/quotes/dashboard/?quote={quote_id}')
