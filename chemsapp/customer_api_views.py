"""JSON reads for the admin app's customer screen.

Like the product side, the dashboard's own views answer with HTML. These
read the same data as JSON; writing still goes through the dashboard's
views, which already answer in JSON and hold the validation.
"""
from django.shortcuts import get_object_or_404

from .customer_dashboard_views import _resolved_prices, _search_customers, _search_groups
from .models import Customer, CustomerGroup
from .staff_api import ok, staff_api


def _money(value):
    """Money as a string, so no precision is lost in JSON."""
    return None if value is None else str(value)


@staff_api
def customer_tree(request):
    """The customers list, for the left side."""
    search = request.GET.get('q', '').strip()
    return ok({
        'customers': [
            {
                'id': customer.pk,
                'name': customer.businessName,
                'email': customer.user.email if customer.user_id else None,
                'group': (
                    {'id': customer.group_id, 'name': customer.group.name}
                    if customer.group_id else None
                ),
            }
            for customer in _search_customers(search)
        ],
    })


@staff_api
def group_tree(request):
    """The groups list, for the left side when ?view=groups."""
    search = request.GET.get('q', '').strip()
    return ok({
        'groups': [
            {
                'id': group.pk,
                'name': group.name,
                'note': group.note,
                'customer_count': group.customers.count(),
            }
            for group in _search_groups(search)
        ],
    })


@staff_api
def customer_detail(request, customer_id):
    """One customer: details, contacts, group, and every price that is not
    the plain recommended retail price.

    The prices come from the dashboard's own _resolved_prices, so this
    screen and the dashboard cannot disagree about which price wins.
    """
    customer = get_object_or_404(
        Customer.objects
        .select_related('user', 'group')
        .prefetch_related('contacts', 'distributors'),
        pk=customer_id,
    )

    return ok({
        'id': customer.pk,
        'name': customer.businessName,
        'phone_number': customer.phoneNumber,
        'cell_phone_number': customer.cellPhoneNumber,
        'address': customer.address,
        'geocoding_detail': customer.geocodingDetail,
        'email': customer.user.email if customer.user_id else None,
        'username': customer.user.username if customer.user_id else None,
        'group': (
            {'id': customer.group_id, 'name': customer.group.name}
            if customer.group_id else None
        ),
        'contacts': [
            {
                'id': contact.pk,
                'name': contact.name,
                'role': contact.role,
                'email': contact.email,
                'phone': contact.phone,
                'receive_report': contact.receive_report,
            }
            for contact in customer.contacts.all()
        ],
        'distributors': [
            {'id': d.pk, 'name': d.businessname} for d in customer.distributors.all()],
        'prices': [
            {
                'variant': {
                    'id': row['variant'].pk,
                    'code': row['variant'].code,
                    'size': row['variant'].size.name if row['variant'].size_id else None,
                    'product': {
                        'id': row['variant'].product_id,
                        'name': row['variant'].product.name,
                    },
                },
                'price': _money(row['price']),
                # 'customer', 'group' or 'rrp': which rule set this price.
                'source': row['source_kind'],
            }
            for row in _resolved_prices(customer)
        ],
    })


@staff_api
def group_detail(request, group_id):
    """One group: its members and the prices set on it."""
    group = get_object_or_404(CustomerGroup, pk=group_id)

    members = group.customers.select_related('user').order_by('businessName')
    prices = (
        group.pricing_variants
        .select_related('product_variant__product', 'product_variant__size')
        .all()
    )

    return ok({
        'id': group.pk,
        'name': group.name,
        'note': group.note,
        'customers': [
            {
                'id': member.pk,
                'name': member.businessName,
                'email': member.user.email if member.user_id else None,
            }
            for member in members
        ],
        'prices': [
            {
                'id': price.pk,
                'price': _money(price.price),
                'name': price.name,
                'min_quantity': price.min_quantity,
                'variant': {
                    'id': price.product_variant_id,
                    'code': price.product_variant.code,
                    'size': (
                        price.product_variant.size.name
                        if price.product_variant.size_id else None
                    ),
                    'product': {
                        'id': price.product_variant.product_id,
                        'name': price.product_variant.product.name,
                    },
                },
            }
            for price in prices
        ],
    })
