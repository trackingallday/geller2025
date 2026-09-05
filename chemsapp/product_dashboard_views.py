"""Product dashboard: one screen to edit a product and everything under it.

The stock admin splits a product across a product page, a variant page and a
pricing page. This dashboard puts them on one page with five tabs, in the
shape of the quote dashboard in quotes/dashboard_views.py.
"""
import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.forms import inlineformset_factory, modelform_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from .forms import PricingVariantForm
from .models import (
    Customer, DilutionVariant, PricingVariant, Product, ProductCategory,
    ProductEquivalency, ProductVariant,
)

# Most rows a search returns. Categories are a short fixed list and ignore
# this when nothing is typed. Customers always apply it: the table grows.
SEARCH_LIMIT = 50

# The order the tabs show in. The first one is the tab a product opens on.
TABS = [
    ('product', 'Product'),
    ('variants', 'Variants'),
    ('customers', 'Customers'),
    ('compliance', 'Compliance'),
    ('dilutions', 'Dilutions'),
    ('prices', 'Prices'),
    ('equivalents', 'Equivalents'),
]

# The tab a product opens on, and the one a bad ?tab= falls back to.
DEFAULT_TAB = TABS[0][0]

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

# The fields of one variant. The bulk formset and the single-variant form
# share this list, so the two cannot drift apart.
VARIANT_FIELDS = [
    'code', 'size', 'pack_size', 'recommended_retail_price', 'barcode',
    'carton_barcode', 'label_code', 'description', 'image', 'label',
]

# The fields that a variant search looks at. This is the list that
# ProductVariantAdmin.search_fields uses, less the product name: the product
# query below already matches on that.
# Shortest search term that also lists variants. Below this the term
# matches too many products to show a variant under each one.
VARIANT_SEARCH_LENGTH = 4

VARIANT_SEARCH_FIELDS = [
    'code', 'barcode', 'carton_barcode', 'label_code', 'size__name',
]

ProductVariantForm = modelform_factory(ProductVariant, fields=VARIANT_FIELDS)

VariantFormSet = inlineformset_factory(
    Product, ProductVariant, fields=VARIANT_FIELDS, extra=1, can_delete=True)

# fk_name is required: ProductEquivalency has two foreign keys to Product.
EquivalencyFormSet = inlineformset_factory(
    Product, ProductEquivalency, fk_name='product',
    fields=['equivalent_product', 'note'],
    extra=1, can_delete=True)

DilutionFormSet = inlineformset_factory(
    ProductVariant, DilutionVariant,
    fields=['application_type', 'value', 'note'],
    extra=1, can_delete=True)


def _dashboard_url(product_id=None, tab=None, search='', variant_id=None):
    """Back to the dashboard, on the same product, tab and variant."""
    url = reverse('product_dashboard')
    params = []
    if product_id:
        params.append(f'product={product_id}')
    if tab:
        params.append(f'tab={tab}')
    if variant_id:
        params.append(f'variant={variant_id}')
    if search:
        params.append(f'q={search}')
    return f'{url}?{"&".join(params)}' if params else url


def _search_products(search):
    """The left list: one row for each product, with its variants under it.

    A row is {'product': product, 'variants': [variant, ...]}. With no search
    term every product shows and no variant shows: the list is a product
    list until the user types.

    A short search term also shows no variants. The first few characters of
    a word match too many products, and a variant under each one makes a
    list too long to read. From VARIANT_SEARCH_LENGTH characters the term is
    specific enough, and every product in the results shows all of its
    variants. The user can then click one without opening the product first.
    """
    products = Product.objects.prefetch_related('variants__size').order_by('name')
    if not search:
        return [{'product': product, 'variants': []} for product in products]

    products = products.filter(
        Q(name__icontains=search) |
        Q(productCode__icontains=search) |
        Q(brand__icontains=search)
    ).distinct()

    if len(search) < VARIANT_SEARCH_LENGTH:
        return [{'product': product, 'variants': []} for product in products]

    variant_query = Q()
    for field in VARIANT_SEARCH_FIELDS:
        variant_query |= Q(**{f'{field}__icontains': search})
    matched = (
        ProductVariant.objects
        .filter(variant_query)
        .select_related('product')
        .order_by('code')
    )

    # A product shows when it matches, or when one of its variants does.
    rows = {product.pk: product for product in products}

    # A product that only a variant matched is not in `rows` yet. Fetch them
    # together, with the same prefetch: every row lists its variants, and
    # variant.product would make one query for each row.
    missing = {v.product_id for v in matched} - set(rows)
    if missing:
        extra = (Product.objects
                 .prefetch_related('variants__size')
                 .filter(pk__in=missing))
        for product in extra:
            rows[product.pk] = product

    # Every product in the results lists all of its variants, not only the
    # ones that matched. The prefetch already holds them, so this is free.
    return [
        {'product': product, 'variants': list(product.variants.all())}
        for product in sorted(rows.values(), key=lambda p: p.name)
    ]


def _focus_variant(product, variant_id):
    """The variant the Variants tab shows in its focus pane.

    An id that belongs to another product is ignored, as an unknown product
    id is. The first variant then takes the focus, so the tab is never empty
    when the product has a variant.
    """
    variants = list(product.variants.all())
    if variant_id:
        for variant in variants:
            if str(variant.pk) == str(variant_id):
                return variant
    return variants[0] if variants else None


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
                'customers__user',
                'productCategory',
                'subCategory',
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
    active_tab = request.GET.get('tab', DEFAULT_TAB)
    if active_tab not in dict(TABS):
        active_tab = DEFAULT_TAB

    product_rows = _search_products(search)
    product = _selected_product(request.GET.get('product', ''))

    context = {
        'product_rows': product_rows,
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
        # The search pickers render the current selection as chips. Give them
        # the id and the name, because the widget value holds only ids.
        context['selected_safety_wears'] = set(
            product.safetyWears.values_list('pk', flat=True))
        context['picker_selected'] = json.dumps({
            'productCategory': [
                {'id': c.pk, 'name': c.name} for c in product.productCategory.all()],
            'subCategory': [
                {'id': c.pk, 'name': c.name} for c in product.subCategory.all()],
        })
        context['dilution_groups'] = [
            {'variant': variant, 'formset': DilutionFormSet(
                instance=variant, prefix=f'dilution-{variant.pk}')}
            for variant in product.variants.all()
        ]

        # The Variants tab: one variant in the focus pane, the rest below it.
        # ?new=1 opens an empty pane, which the save creates as a new row.
        is_new_variant = request.GET.get('new') == '1'
        focus_variant = None if is_new_variant else _focus_variant(
            product, request.GET.get('variant', ''))
        context['is_new_variant'] = is_new_variant
        context['focus_variant'] = focus_variant
        context['focus_form'] = ProductVariantForm(instance=focus_variant)
        context['other_variants'] = [
            variant for variant in product.variants.all()
            if focus_variant is None or variant.pk != focus_variant.pk
        ]
        context['focus_dilution_formset'] = DilutionFormSet(
            instance=focus_variant,
            prefix=f'dilution-{focus_variant.pk}') if focus_variant else None

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


def _variant_json(variant):
    """One variant as the row data the Variants tab shows."""
    return {
        'id': variant.pk,
        'code': variant.code or '',
        'size': str(variant.size) if variant.size else '',
        'pack_size': variant.pack_size,
        'price': str(variant.recommended_retail_price)
        if variant.recommended_retail_price is not None else '',
        'image_url': variant.image.url if variant.image else '',
    }


def _is_ajax(request):
    """True when the focus pane posted by fetch, not as a plain form."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _save_variant_form(request, instance, product):
    """Validate and save one variant.

    The focus pane posts by fetch and stays on the page, so the answer holds
    the new row data on success and the field errors on failure. With no
    JavaScript the same form posts normally. A browser must then get the
    page back, not raw JSON, so this redirects to the Variants tab.
    """
    form = ProductVariantForm(request.POST, request.FILES, instance=instance)
    if not form.is_valid():
        if not _is_ajax(request):
            messages.error(
                request, f'The variant did not save: {form.errors.as_text()}')
            return redirect(_dashboard_url(
                product.pk, 'variants',
                variant_id=instance.pk if instance else None))
        return JsonResponse(
            {'ok': False, 'errors': form.errors.get_json_data(escape_html=True)},
            status=400)

    variant = form.save(commit=False)
    variant.product = product
    variant.save()
    form.save_m2m()

    if not _is_ajax(request):
        messages.success(request, 'Saved the variant.')
        return redirect(_dashboard_url(product.pk, 'variants', variant_id=variant.pk))
    return JsonResponse({'ok': True, 'variant': _variant_json(variant)})


@staff_member_required
def save_one_variant(request, variant_id):
    """Save the variant in the focus pane of the Variants tab."""
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(variant.product_id, 'variants',
                                       variant_id=variant.pk))
    return _save_variant_form(request, variant, variant.product)


@staff_member_required
def create_variant(request, product_id):
    """Add one variant to this product, from the empty focus pane."""
    product = get_object_or_404(Product, pk=product_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(product.pk, 'variants'))
    return _save_variant_form(request, None, product)


@staff_member_required
def delete_variant(request, variant_id):
    """Remove one variant from the Variants tab."""
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    product_id = variant.product_id
    if request.method == 'POST':
        variant.delete()
        messages.success(request, 'Removed the variant.')
    return redirect(_dashboard_url(product_id, 'variants'))


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
def add_product_customer(request, product_id):
    """Link one customer to this product, from the Customers tab."""
    product = get_object_or_404(Product, pk=product_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(product.pk, 'customers'))

    # The picker allows more than one chip before saving, so read them all.
    customer_ids = request.POST.getlist('customer')
    customers = Customer.objects.filter(pk__in=customer_ids)
    if not customers:
        messages.error(request, 'Select a customer first.')
        return redirect(_dashboard_url(product.pk, 'customers'))

    added = []
    for customer in customers:
        # add() on a many-to-many ignores a row that is already there, so a
        # repeat cannot create a duplicate.
        customer.products.add(product)
        added.append(customer.businessName or customer.user.username)
    messages.success(request, 'Added {} to {}.'.format(', '.join(added), product.name))
    return redirect(_dashboard_url(product.pk, 'customers'))


@staff_member_required
def remove_product_customer(request, product_id, customer_id):
    """Unlink one customer from this product."""
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=customer_id)
        customer.products.remove(product)
        messages.success(
            request, f'Removed {customer.businessName} from {product.name}.')
    return redirect(_dashboard_url(product.pk, 'customers'))


@staff_member_required
def customer_search(request):
    """Customers matching ?q=, for the "add customer" box on the Prices tab.

    Customers that already have a price for ?product= are left out. The form
    rejects them anyway, so offering them would only produce an error.
    """
    search = request.GET.get('q', '').strip()
    customers = Customer.objects.select_related('user')

    # ?exclude_priced=<product id> leaves out customers that already have a
    # price for that product. ?exclude_linked=<product id> leaves out those
    # already linked to it. Each picker asks for the one it needs.
    priced_for = request.GET.get('exclude_priced', '')
    if priced_for:
        customers = customers.exclude(pricing_variants__product_id=priced_for)

    linked_to = request.GET.get('exclude_linked', '')
    if linked_to:
        customers = customers.exclude(products__id=linked_to)

    if search:
        customers = customers.filter(
            Q(businessName__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )

    customers = customers.order_by('businessName')[:SEARCH_LIMIT]
    results = [
        {'id': customer.pk,
         'name': customer.businessName or customer.user.get_full_name() or customer.user.username,
         'detail': customer.user.email}
        for customer in customers
    ]
    return JsonResponse({'results': results})


@staff_member_required
def product_list(request):
    """The rows of the left list, for the search box.

    This answers with HTML, not JSON. The page and the live search render the
    same include, so a row cannot look one way on load and another way after
    a search.
    """
    search = request.GET.get('q', '').strip()
    active_tab = request.GET.get('tab', DEFAULT_TAB)
    if active_tab not in dict(TABS):
        active_tab = DEFAULT_TAB

    product = _selected_product(request.GET.get('product', ''))
    focus_variant = None
    if product is not None:
        focus_variant = _focus_variant(product, request.GET.get('variant', ''))

    return TemplateResponse(request, 'chemsapp/_product_list.html', {
        'product_rows': _search_products(search),
        'product': product,
        'focus_variant': focus_variant,
        'search': search,
        'active_tab': active_tab,
    })


@staff_member_required
def category_search(request):
    """Product categories matching ?q=, for the search-and-add pickers.

    With no search term this returns every category. The list is short and
    fixed, so staff can browse it without typing.
    """
    search = request.GET.get('q', '').strip()
    categories = ProductCategory.objects.order_by('name')
    if search:
        categories = categories.filter(name__icontains=search)[:SEARCH_LIMIT]

    results = [
        {'id': category.pk, 'name': category.name, 'detail': ''}
        for category in categories
    ]
    return JsonResponse({'results': results})


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
