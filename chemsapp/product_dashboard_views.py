"""Product dashboard: one screen to edit a product and everything under it.

The stock admin splits a product across a product page, a variant page and a
pricing page. This dashboard puts them on one page with five tabs, in the
shape of the quote dashboard in quotes/dashboard_views.py.
"""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import inlineformset_factory, modelform_factory
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from .forms import PricingVariantForm
from .models import (
    DilutionVariant, PricingVariant, Product, ProductEquivalency, ProductVariant,
)

TABS = [
    ('prices', 'Prices'),
    ('product', 'Product'),
    ('variants', 'Variants'),
    ('compliance', 'Compliance'),
    ('dilutions', 'Dilutions'),
    ('equivalents', 'Equivalents'),
]

PRODUCT_FIELDS = [
    'name', 'brand', 'product_range', 'subheading', 'description', 'directions',
    'properties', 'bom', 'primaryImageLink', 'secondaryImageLink', 'public',
    'productCategory', 'subCategory', 'safetyWears',
]
COMPLIANCE_FIELDS = [
    'infoSheet', 'sdsSheet', 'application_sheet', 'mpi_approval',
    'mpi_approval_sheet', 'application', 'procedure',
]

# The documents shown as upload rows on the Compliance tab.
COMPLIANCE_DOCUMENTS = [
    ('infoSheet', 'Product Information Sheet'),
    ('sdsSheet', 'Safety Data Sheet'),
    ('application_sheet', 'Product Application Sheet'),
    ('mpi_approval_sheet', 'MPI Approval'),
]

ProductDetailsForm = modelform_factory(Product, fields=PRODUCT_FIELDS)
ProductComplianceForm = modelform_factory(Product, fields=COMPLIANCE_FIELDS)
ProductPriceForm = modelform_factory(Product, fields=['recommended_retail_price'])

VariantFormSet = inlineformset_factory(
    Product, ProductVariant,
    fields=['code', 'size', 'pack_size', 'barcode', 'carton_barcode',
            'label_code', 'description', 'image', 'label'],
    extra=1, can_delete=True)

# fk_name is required: ProductEquivalency has two foreign keys to Product.
EquivalencyFormSet = inlineformset_factory(
    Product, ProductEquivalency, fk_name='product',
    fields=['equivalent_product', 'note'],
    extra=1, can_delete=True)

DilutionFormSet = inlineformset_factory(
    ProductVariant, DilutionVariant,
    fields=['application_type', 'value', 'note'],
    extra=1, can_delete=True)


def _dashboard_url(product_id=None, tab=None, search=''):
    """Back to the dashboard, on the same product and the same tab."""
    url = reverse('product_dashboard')
    params = []
    if product_id:
        params.append(f'product={product_id}')
    if tab:
        params.append(f'tab={tab}')
    if search:
        params.append(f'q={search}')
    return f'{url}?{"&".join(params)}' if params else url


def _selected_product(product_id):
    """The product with everything the editor shows, or None.

    An unknown id is not an error. The page then shows the list with no
    product selected, as the quote dashboard does.
    """
    if not product_id:
        return None
    try:
        return (
            Product.objects
            .prefetch_related(
                'variants__size',
                'variants__dilutions__application_type',
                'pricing_variants__customers',
                'equivalents__equivalent_product',
                'productCategory',
                'safetyWears',
            )
            .get(pk=product_id)
        )
    except (Product.DoesNotExist, ValueError):
        return None


@staff_member_required
def product_dashboard(request):
    """Product list on the left, the tabbed editor on the right."""
    search = request.GET.get('q', '').strip()
    active_tab = request.GET.get('tab', 'prices')
    if active_tab not in dict(TABS):
        active_tab = 'prices'

    products = Product.objects.prefetch_related('variants').order_by('name')
    if search:
        products = products.filter(name__icontains=search) | \
            products.filter(productCode__icontains=search) | \
            products.filter(brand__icontains=search)
        products = products.distinct()

    product = _selected_product(request.GET.get('product', ''))

    context = {
        'products': products,
        'product': product,
        'search': search,
        'tabs': TABS,
        'active_tab': active_tab,
    }

    if product is not None:
        context['details_form'] = ProductDetailsForm(instance=product)
        context['compliance_form'] = ProductComplianceForm(instance=product)
        context['price_form'] = ProductPriceForm(instance=product)
        context['variant_formset'] = VariantFormSet(instance=product)
        context['equivalency_formset'] = EquivalencyFormSet(instance=product)
        context['pricing_form'] = PricingVariantForm(initial={'product': product})
        context['compliance_documents'] = [
            {'field': context['compliance_form'][name], 'label': label,
             'file': getattr(product, name)}
            for name, label in COMPLIANCE_DOCUMENTS
        ]
        context['dilution_groups'] = [
            {'variant': variant, 'formset': DilutionFormSet(
                instance=variant, prefix=f'dilution-{variant.pk}')}
            for variant in product.variants.all()
        ]

    return TemplateResponse(request, 'chemsapp/product_dashboard.html', context)


@staff_member_required
def save_product_details(request, product_id):
    """Save the Product tab."""
    product = get_object_or_404(Product, pk=product_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(product.pk, 'product'))

    form = ProductDetailsForm(request.POST, request.FILES, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, f'Saved the details of {product.name}.')
    else:
        messages.error(request, f'The details did not save: {form.errors.as_text()}')
    return redirect(_dashboard_url(product.pk, 'product'))


@staff_member_required
def save_product_compliance(request, product_id):
    """Save the Compliance tab: the documents and the usage text."""
    product = get_object_or_404(Product, pk=product_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(product.pk, 'compliance'))

    form = ProductComplianceForm(request.POST, request.FILES, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, f'Saved the documents of {product.name}.')
    else:
        messages.error(request, f'The documents did not save: {form.errors.as_text()}')
    return redirect(_dashboard_url(product.pk, 'compliance'))


@staff_member_required
def save_product_rrp(request, product_id):
    """Save the recommended retail price at the top of the Prices tab."""
    product = get_object_or_404(Product, pk=product_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(product.pk, 'prices'))

    form = ProductPriceForm(request.POST, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, 'Saved the recommended retail price.')
    else:
        messages.error(request, f'The price did not save: {form.errors.as_text()}')
    return redirect(_dashboard_url(product.pk, 'prices'))


@staff_member_required
def save_variants(request, product_id):
    """Save the Variants table: add, edit and remove rows together."""
    product = get_object_or_404(Product, pk=product_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(product.pk, 'variants'))

    formset = VariantFormSet(request.POST, request.FILES, instance=product)
    if formset.is_valid():
        formset.save()
        messages.success(request, f'Saved the variants of {product.name}.')
    else:
        messages.error(request, f'The variants did not save: {formset.errors}')
    return redirect(_dashboard_url(product.pk, 'variants'))


@staff_member_required
def save_equivalents(request, product_id):
    """Save the Equivalents tab: products that do the same job."""
    product = get_object_or_404(Product, pk=product_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(product.pk, 'equivalents'))

    formset = EquivalencyFormSet(request.POST, instance=product)
    if formset.is_valid():
        formset.save()
        messages.success(request, f'Saved the equivalents of {product.name}.')
    else:
        messages.error(request, f'The equivalents did not save: {formset.errors}')
    return redirect(_dashboard_url(product.pk, 'equivalents'))


@staff_member_required
def save_dilutions(request, variant_id):
    """Save the dilution rows of one variant."""
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(variant.product_id, 'dilutions'))

    formset = DilutionFormSet(
        request.POST, instance=variant, prefix=f'dilution-{variant.pk}')
    if formset.is_valid():
        formset.save()
        messages.success(request, f'Saved the dilutions of {variant}.')
    else:
        messages.error(request, f'The dilutions did not save: {formset.errors}')
    return redirect(_dashboard_url(variant.product_id, 'dilutions'))


@staff_member_required
def save_pricing_variant(request, product_id):
    """Add or edit one price on the Prices tab.

    PricingVariantForm refuses to give one customer two prices for the same
    product. That rule holds here too.
    """
    product = get_object_or_404(Product, pk=product_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(product.pk, 'prices'))

    pricing_variant = None
    pricing_variant_id = request.POST.get('pricing_variant_id')
    if pricing_variant_id:
        pricing_variant = get_object_or_404(
            PricingVariant, pk=pricing_variant_id, product=product)

    form = PricingVariantForm(request.POST, instance=pricing_variant)
    if form.is_valid():
        form.save()
        messages.success(request, 'Saved the price.')
    else:
        messages.error(request, f'The price did not save: {form.errors.as_text()}')
    return redirect(_dashboard_url(product.pk, 'prices'))


@staff_member_required
def delete_pricing_variant(request, pricing_variant_id):
    """Remove one price from the Prices tab."""
    pricing_variant = get_object_or_404(PricingVariant, pk=pricing_variant_id)
    product_id = pricing_variant.product_id
    if request.method == 'POST':
        pricing_variant.delete()
        messages.success(request, 'Removed the price.')
    return redirect(_dashboard_url(product_id, 'prices'))
