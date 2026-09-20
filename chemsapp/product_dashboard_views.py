"""Product dashboard: one screen to edit a product and everything under it.

The stock admin splits a product across a product page, a variant page and a
pricing page. This dashboard puts them on one page with five tabs, in the
shape of the quote dashboard in quotes/dashboard_views.py.
"""
import base64
import json
import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.forms import inlineformset_factory, modelform_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from rest_framework.authtoken.models import Token

from .forms import GroupPricingVariantForm, PricingVariantForm
from .models import (
    Customer, CustomerGroup, DilutionVariant, GroupPricingVariant,
    PricingVariant, Product, ProductCategory, ProductEquivalency,
    ProductVariant,
)
from .serializers import ProductSyncSerializer

logger = logging.getLogger(__name__)

# Most rows a search returns. Categories are a short fixed list and ignore
# this when nothing is typed. Customers always apply it: the table grows.
SEARCH_LIMIT = 50

# The order the tabs show in, for the PRODUCT view. The first one is the tab
# a product opens on. Variants is not a tab: a variant is its own view, with
# no tabs, reached only from the sidebar. Prices and Dilutions moved into
# that view for the same reason — they are variant data, not product data.
TABS = [
    ('product', 'Product'),
    ('customers', 'Customers'),
    ('compliance', 'Compliance'),
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


def _search_products(search, always_expand=None):
    """The left list: one row for each product, with its variants under it.

    A row is {'product': product, 'variants': [variant, ...]}. With no search
    term every product shows and no variant shows: the list is a product
    list until the user types.

    A short search term also shows no variants. The first few characters of
    a word match too many products, and a variant under each one makes a
    list too long to read. From VARIANT_SEARCH_LENGTH characters the term is
    specific enough, and every product in the results shows all of its
    variants. The user can then click one without opening the product first.

    always_expand is the id of the product currently open in a variant view.
    A variant is only reachable from this list, so the product being worked
    on must show its variants regardless of the search — otherwise a short
    search could hide the one product the user needs a variant of.
    """
    products = Product.objects.prefetch_related('variants__size').order_by('name')
    show_variants = search and len(search) >= VARIANT_SEARCH_LENGTH

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(productCode__icontains=search) |
            Q(brand__icontains=search)
        ).distinct()

    rows = {product.pk: product for product in products}
    matched_variants_by_product = {}

    if show_variants:
        variant_query = Q()
        for field in VARIANT_SEARCH_FIELDS:
            variant_query |= Q(**{f'{field}__icontains': search})
        matched = (
            ProductVariant.objects
            .filter(variant_query)
            .select_related('product')
            .order_by('code')
        )
        for variant in matched:
            matched_variants_by_product.setdefault(variant.product_id, []).append(variant)

        # A product that only a variant matched is not in `rows` yet.
        missing = set(matched_variants_by_product) - set(rows)
        if missing:
            extra = (Product.objects
                     .prefetch_related('variants__size')
                     .filter(pk__in=missing))
            for product in extra:
                rows[product.pk] = product

    if always_expand and always_expand not in rows:
        extra_product = (
            Product.objects.prefetch_related('variants__size')
            .filter(pk=always_expand).first())
        if extra_product:
            rows[always_expand] = extra_product

    def variants_for(product):
        if product.pk == always_expand or show_variants:
            # Every product in the results lists all of its variants, not
            # only the ones that matched. The prefetch already holds them.
            return list(product.variants.all())
        return []

    return [
        {'product': product, 'variants': variants_for(product)}
        for product in sorted(rows.values(), key=lambda p: p.name)
    ]


def _focus_variant(product, variant_id):
    """The variant the page shows on its own, with no tabs, or None.

    The sidebar is what picks a product or a variant now, so only an
    explicit, valid ?variant= puts the page in variant mode. An id that
    belongs to another product is ignored, as an unknown id is — the page
    then shows the product, not a variant it was not asked for.
    """
    if not variant_id:
        return None
    for variant in product.variants.all():
        if str(variant.pk) == str(variant_id):
            return variant
    return None


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
                'variants__pricing_variants__customers',
                'variants__group_pricing_variants__customer_group',
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
    """Product list on the left. The right side is one of three things:
    nothing selected, a product with its tabs, or one variant with no tabs.

    The sidebar is what switches between a product and a variant — there is
    no tab for it. Selecting a variant replaces the whole right side with
    that variant alone: its fields, its price, its dilutions. Selecting a
    product shows the product's own tabs, none of which are variant data.
    """
    search = request.GET.get('q', '').strip()
    active_tab = request.GET.get('tab', DEFAULT_TAB)
    if active_tab not in dict(TABS):
        active_tab = DEFAULT_TAB

    product = _selected_product(request.GET.get('product', ''))

    is_new_variant = request.GET.get('new') == '1'
    focus_variant = None
    if product is not None and not is_new_variant:
        focus_variant = _focus_variant(product, request.GET.get('variant', ''))

    # True when the right side must show one variant alone, with no tabs.
    # A plain Python bool, not a template expression: Django's {% if %} has
    # no parentheses, so `product and (focus_variant or is_new_variant)`
    # cannot be written correctly in the template.
    showing_variant = product is not None and (focus_variant is not None or is_new_variant)

    # The open product's own variants always show in the sidebar, however
    # short the search — it is the one product the user is working on,
    # whether that shows as its tabs or as one of its variants, so a variant
    # of it must stay one click away either way.
    open_product_id = product.pk if product is not None else None
    product_rows = _search_products(search, always_expand=open_product_id)

    context = {
        'product_rows': product_rows,
        'product': product,
        'search': search,
        'tabs': TABS,
        'active_tab': active_tab,
        'is_new_variant': is_new_variant,
        'focus_variant': focus_variant,
        'showing_variant': showing_variant,
    }

    if product is not None and not showing_variant:
        # The product view. A variant is never shown here — Prices and
        # Dilutions moved into the variant's own view, and Variants is not
        # a tab any more.
        context['details_form'] = ProductDetailsForm(instance=product)
        context['compliance_form'] = ProductComplianceForm(instance=product)
        context['equivalency_formset'] = EquivalencyFormSet(instance=product)
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

    if showing_variant:
        # The variant view: one variant, full width, no tabs.
        context['focus_form'] = ProductVariantForm(instance=focus_variant)
        context['focus_dilution_formset'] = DilutionFormSet(
            instance=focus_variant,
            prefix=f'dilution-{focus_variant.pk}') if focus_variant else None
        # Customer prices and group prices for the focused variant. A new
        # variant has none yet — it has no pk to hang a price off until it
        # is first saved.
        context['pricing_form'] = PricingVariantForm(
            initial={'product_variant': focus_variant}) if focus_variant else None
        context['group_pricing_form'] = GroupPricingVariantForm(
            initial={'product_variant': focus_variant}) if focus_variant else None
        context['all_groups'] = CustomerGroup.objects.order_by('name')

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

    Customers that already have a price for ?exclude_priced_variant= are left
    out. The form rejects them anyway, so offering them would only produce an
    error.
    """
    search = request.GET.get('q', '').strip()
    customers = Customer.objects.select_related('user')

    # ?exclude_priced_variant=<variant id> leaves out customers that already
    # have a price for that variant. ?exclude_linked=<product id> leaves out
    # those already linked to that product. Each picker asks for the one it
    # needs.
    priced_for = request.GET.get('exclude_priced_variant', '')
    if priced_for:
        customers = customers.exclude(pricing_variants__product_variant_id=priced_for)

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
    is_new_variant = request.GET.get('new') == '1'
    focus_variant = None
    if product is not None and not is_new_variant:
        focus_variant = _focus_variant(product, request.GET.get('variant', ''))

    showing_variant = product is not None and (focus_variant is not None or is_new_variant)
    open_product_id = product.pk if product is not None else None

    return TemplateResponse(request, 'chemsapp/_product_list.html', {
        'product_rows': _search_products(search, always_expand=open_product_id),
        'product': product,
        'focus_variant': focus_variant,
        'is_new_variant': is_new_variant,
        'showing_variant': showing_variant,
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
def save_pricing_variant(request, variant_id):
    """Add or edit one customer price, from the Variants tab focus pane.

    PricingVariantForm refuses to give one customer two prices for the same
    variant. That rule holds here too.
    """
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(variant.product_id, 'variants', variant_id=variant.pk))

    pricing_variant = None
    pricing_variant_id = request.POST.get('pricing_variant_id')
    if pricing_variant_id:
        pricing_variant = get_object_or_404(
            PricingVariant, pk=pricing_variant_id, product_variant=variant)

    form = PricingVariantForm(request.POST, instance=pricing_variant)
    if form.is_valid():
        form.save()
        messages.success(request, 'Saved the price.')
    else:
        messages.error(request, f'The price did not save: {form.errors.as_text()}')
    return redirect(_dashboard_url(variant.product_id, 'variants', variant_id=variant.pk))


@staff_member_required
def delete_pricing_variant(request, pricing_variant_id):
    """Remove one price from the Variants tab focus pane."""
    pricing_variant = get_object_or_404(PricingVariant, pk=pricing_variant_id)
    variant = pricing_variant.product_variant
    if request.method == 'POST':
        pricing_variant.delete()
        messages.success(request, 'Removed the price.')
    return redirect(_dashboard_url(variant.product_id, 'variants', variant_id=variant.pk))


@staff_member_required
def save_group_pricing_variant(request, variant_id):
    """Add or edit one group price, from the variant focus pane.

    GroupPricingVariantForm refuses to give one group two prices for the
    same variant. That rule holds here too.
    """
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    if request.method != 'POST':
        return redirect(_dashboard_url(variant.product_id, 'variants', variant_id=variant.pk))

    group_pricing_variant = None
    group_pricing_variant_id = request.POST.get('group_pricing_variant_id')
    if group_pricing_variant_id:
        group_pricing_variant = get_object_or_404(
            GroupPricingVariant, pk=group_pricing_variant_id, product_variant=variant)

    form = GroupPricingVariantForm(request.POST, instance=group_pricing_variant)
    if form.is_valid():
        form.save()
        messages.success(request, 'Saved the group price.')
    else:
        messages.error(request, f'The group price did not save: {form.errors.as_text()}')
    return redirect(_dashboard_url(variant.product_id, 'variants', variant_id=variant.pk))


@staff_member_required
def delete_group_pricing_variant(request, group_pricing_variant_id):
    """Remove one group price from the variant focus pane."""
    group_pricing_variant = get_object_or_404(
        GroupPricingVariant, pk=group_pricing_variant_id)
    variant = group_pricing_variant.product_variant
    if request.method == 'POST':
        group_pricing_variant.delete()
        messages.success(request, 'Removed the group price.')
    return redirect(_dashboard_url(variant.product_id, 'variants', variant_id=variant.pk))


def _sync_product_to_geller_ai(product, user, include_pdfs):
    """Push one product's data into geller_ai's real-time ingest endpoint.

    Returns the parsed JSON response on success. Raises requests.Timeout or
    requests.RequestException on failure — callers decide how to surface
    that (the dashboard button must not swallow it: syncing is the whole
    point of the click, unlike the best-effort OnePageCRM integration).

    The payload is built from ProductSyncSerializer, which is a hand-written
    allowlist that never includes pricing — see that serializer's docstring.
    Do not extend this function to pull in PricingVariant/GroupPricingVariant
    or chemsapp.pricing.resolve_price.
    """
    detail = ProductSyncSerializer(product).data

    payload = {'detail': detail, 'include_pdfs': include_pdfs}
    if include_pdfs:
        if product.infoSheet:
            with product.infoSheet.open('rb') as f:
                payload['info_sheet_b64'] = base64.b64encode(f.read()).decode('ascii')
        if product.sdsSheet:
            with product.sdsSheet.open('rb') as f:
                payload['sds_b64'] = base64.b64encode(f.read()).decode('ascii')

    token, _ = Token.objects.get_or_create(user=user)
    response = requests.post(
        f"{settings.GELLER_AI_ENDPOINT}/ingest/product/{product.pk}",
        json=payload,
        headers={'Authorization': f'Token {token.key}'},
        timeout=settings.GELLER_AI_SYNC_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@staff_member_required
def sync_product_to_geller_ai(request, product_id):
    """Push one product's current data into geller_ai's search index.

    Unlike the other dashboard actions this is AJAX-only: there is no
    plain-form fallback, since the button always posts by fetch.
    """
    product = get_object_or_404(Product, pk=product_id)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)

    include_pdfs = request.POST.get('include_pdfs') == 'true'

    try:
        data = _sync_product_to_geller_ai(product, request.user, include_pdfs)
    except requests.Timeout:
        logger.warning('Geller AI sync timed out for product %s', product.pk)
        return JsonResponse(
            {'ok': False, 'error': 'Geller AI timed out. Try again.'}, status=504)
    except requests.RequestException as e:
        logger.warning('Geller AI sync failed for product %s: %s', product.pk, e)
        return JsonResponse(
            {'ok': False, 'error': 'Could not reach Geller AI.'}, status=502)

    return JsonResponse(data)
