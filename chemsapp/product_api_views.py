"""JSON reads for the admin app's product screen.

The dashboard's own views answer with HTML: the sidebar is a template, and
the right side is a set of Django forms. The admin app needs the same data
as JSON, so these endpoints read it. Writing still goes through the
dashboard's existing views, which already answer in JSON, so validation
stays in the forms that have always held it.
"""
from django.shortcuts import get_object_or_404

from .models import (
    ApplicationType, CustomerGroup, Product, ProductCategory, ProductVariant,
    SafetyWear,
)
from .pricing import resolve_price
from .product_dashboard_views import COMPLIANCE_DOCUMENTS, _search_products
from .staff_api import ok, staff_api


def _file(field):
    """A file field as {name, url}, or None when empty."""
    if not field:
        return None
    try:
        return {'name': field.name.rsplit('/', 1)[-1], 'url': field.url}
    except ValueError:
        return None


def _variant_row(variant):
    """A variant as the sidebar and the variant view both list them."""
    return {
        'id': variant.pk,
        'code': variant.code,
        'size': variant.size.name if variant.size_id else None,
        'size_id': variant.size_id,
        'pack_size': variant.pack_size,
        'recommended_retail_price': _decimal(variant.recommended_retail_price),
        'barcode': variant.barcode,
        'carton_barcode': variant.carton_barcode,
        'label_code': variant.label_code,
        'description': variant.description,
        'image': _file(variant.image),
        'label': _file(variant.label),
    }


def _decimal(value):
    """Money as a string, so no precision is lost in JSON."""
    return None if value is None else str(value)


@staff_api
def product_tree(request):
    """The left list: products, with variants under them when the search is
    specific enough. Mirrors what the dashboard template renders.
    """
    search = request.GET.get('q', '').strip()
    expand = request.GET.get('expand', '')
    always_expand = int(expand) if expand.isdigit() else None

    rows = _search_products(search, always_expand=always_expand)
    return ok({
        'products': [
            {
                'id': row['product'].pk,
                'name': row['product'].name,
                'code': row['product'].productCode,
                'brand': row['product'].brand,
                'variants': [_variant_row(v) for v in row['variants']],
            }
            for row in rows
        ],
    })


@staff_api
def product_detail(request, product_id):
    """One product: its own fields, its compliance documents, its variants,
    its equivalents and the customers given a price on it.
    """
    product = get_object_or_404(
        Product.objects
        .prefetch_related(
            'variants__size', 'productCategory', 'subCategory', 'safetyWears',
            'equivalents__equivalent_product', 'customers')
        .select_related(),
        pk=product_id,
    )

    return ok({
        'id': product.pk,
        'name': product.name,
        'code': product.productCode,
        'brand': product.brand,
        'product_range': product.product_range,
        'subheading': product.subheading,
        'description': product.description,
        'directions': product.directions,
        'properties': product.properties,
        'bom': product.bom,
        'public': product.public,
        'application': product.application,
        'procedure': product.procedure,
        'mpi_approval': product.mpi_approval,
        'primary_image': _file(product.primaryImageLink),
        'secondary_image': _file(product.secondaryImageLink),
        'categories': [
            {'id': c.pk, 'name': c.name} for c in product.productCategory.all()],
        'sub_categories': [
            {'id': c.pk, 'name': c.name} for c in product.subCategory.all()],
        'safety_wears': [
            {'id': s.pk, 'name': s.name} for s in product.safetyWears.all()],
        'documents': [
            {'field': name, 'label': label, 'file': _file(getattr(product, name))}
            for name, label in COMPLIANCE_DOCUMENTS
        ],
        'variants': [_variant_row(v) for v in product.variants.all()],
        'equivalents': [
            {
                'id': e.pk,
                'product': {
                    'id': e.equivalent_product_id,
                    'name': e.equivalent_product.name,
                } if e.equivalent_product_id else None,
                'note': e.note,
            }
            for e in product.equivalents.all()
        ],
        'customers': [
            {'id': c.pk, 'name': c.businessName} for c in product.customers.all()],
    })


@staff_api
def variant_detail(request, variant_id):
    """One variant: its fields, its dilutions, and every price on it.

    Prices come back with the source that won, from the same resolver the
    quote builder uses, so this screen and a quote can never disagree.
    """
    variant = get_object_or_404(
        ProductVariant.objects
        .select_related('size', 'product')
        .prefetch_related(
            'dilutions__application_type',
            'pricing_variants__customers',
            'group_pricing_variants__customer_group'),
        pk=variant_id,
    )

    return ok({
        **_variant_row(variant),
        'product': {'id': variant.product_id, 'name': variant.product.name},
        'dilutions': [
            {
                'id': d.pk,
                'application_type': {
                    'id': d.application_type_id,
                    'name': d.application_type.name,
                    'unit_label': d.application_type.unit_label,
                } if d.application_type_id else None,
                'value': _decimal(d.value),
                'note': d.note,
            }
            for d in variant.dilutions.all()
        ],
        'customer_prices': [
            {
                'id': p.pk,
                'price': _decimal(p.price),
                'min_quantity': p.min_quantity,
                'customers': [
                    {'id': c.pk, 'name': c.businessName} for c in p.customers.all()],
            }
            for p in variant.pricing_variants.all()
        ],
        'group_prices': [
            {
                'id': g.pk,
                'price': _decimal(g.price),
                'group': {
                    'id': g.customer_group_id,
                    'name': g.customer_group.name,
                } if g.customer_group_id else None,
            }
            for g in variant.group_pricing_variants.all()
        ],
        # No customer, so this is the fallback every price is measured against.
        'default_price': _price_payload(resolve_price(variant, None)),
    })


def _price_payload(resolved):
    price, source = resolved
    return {'price': _decimal(price), 'source': source}


@staff_api
def reference_data(request):
    """The lookup lists the product forms need for their pickers."""
    return ok({
        'categories': [
            {'id': c.pk, 'name': c.name, 'is_sub': c.isSubCategory}
            for c in ProductCategory.objects.order_by('name')
        ],
        'safety_wears': [
            {'id': s.pk, 'name': s.name} for s in SafetyWear.objects.order_by('name')],
        'application_types': [
            {
                'id': a.pk,
                'name': a.name,
                'unit_label': a.unit_label,
                'value_kind': a.value_kind,
            }
            for a in ApplicationType.objects.filter(is_active=True).order_by('sort_order', 'name')
        ],
        'customer_groups': [
            {'id': g.pk, 'name': g.name} for g in CustomerGroup.objects.order_by('name')],
    })
