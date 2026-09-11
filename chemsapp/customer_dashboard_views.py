"""Customer dashboard: one screen to see customers and to run groups.

The screen has two views, chosen by ?view=. "customers" (the default) is a
searchable list of customers on the left and one customer's editor on the
right. "groups" is a searchable list of customer groups on the left and, on
the right, one group with a search-and-add box to put many customers in it
at once.

A customer is in one group at a time. Customer.group is a ForeignKey, so the
database holds that rule. The customer editor changes the group one customer
at a time with a <select>. The groups view changes it many customers at a
time from the group side.

This file follows the shape of chemsapp/product_dashboard_views.py.
"""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.forms import inlineformset_factory, modelform_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from .models import (
    Customer, CustomerContact, CustomerGroup, GroupPricingVariant,
    ProductVariant,
)
from .pricing import resolve_price

# Most rows a search returns. The customer table grows, so the list always
# applies this limit.
SEARCH_LIMIT = 50

# The two views the dashboard switches between. The first one is the default.
VIEWS = [
    ('customers', 'Customers'),
    ('groups', 'Groups'),
]
DEFAULT_VIEW = VIEWS[0][0]

# The customer's own fields that the editor shows. Customer inherits Profile,
# so businessName, phoneNumber, cellPhoneNumber and address come from there.
# The linked User (name, email) stays in Django admin.
CUSTOMER_FIELDS = [
    'businessName', 'phoneNumber', 'cellPhoneNumber', 'address',
    'geocodingDetail',
]

CustomerDetailsForm = modelform_factory(Customer, fields=CUSTOMER_FIELDS)

CONTACT_FIELDS = ['name', 'role', 'email', 'phone', 'receive_report']

ContactFormSet = inlineformset_factory(
    Customer, CustomerContact, fields=CONTACT_FIELDS, extra=1, can_delete=True)


def _dashboard_url(view=None, customer_id=None, group_id=None, search=''):
    """Back to the dashboard, on the same view, row and search."""
    url = reverse('customer_dashboard')
    params = []
    if view:
        params.append(f'view={view}')
    if customer_id:
        params.append(f'customer={customer_id}')
    if group_id:
        params.append(f'group={group_id}')
    if search:
        params.append(f'q={search}')
    return f'{url}?{"&".join(params)}' if params else url


def _search_customers(search):
    """The rows of the customers list, newest business name order."""
    customers = Customer.objects.select_related('user', 'group').order_by('businessName')
    if search:
        customers = customers.filter(
            Q(businessName__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        ).distinct()
    return customers[:SEARCH_LIMIT]


def _search_groups(search):
    """The rows of the groups list, with a member count on each."""
    groups = (
        CustomerGroup.objects
        .annotate(member_count=Count('customers'))
        .order_by('name')
    )
    if search:
        groups = groups.filter(name__icontains=search)
    return groups


def _selected_customer(customer_id):
    """The customer the editor shows, or None. An unknown id is not an error."""
    if not customer_id:
        return None
    try:
        return (
            Customer.objects
            .select_related('user', 'group')
            .prefetch_related('contacts')
            .get(pk=customer_id)
        )
    except (Customer.DoesNotExist, ValueError):
        return None


def _selected_group(group_id):
    """The group the right side shows, or None. An unknown id is not an error."""
    if not group_id:
        return None
    try:
        return (
            CustomerGroup.objects
            .prefetch_related('customers__user')
            .get(pk=group_id)
        )
    except (CustomerGroup.DoesNotExist, ValueError):
        return None


def _resolved_prices(customer):
    """One row for each variant that has a non-RRP price for this customer.

    A row is {'variant', 'price', 'source_kind'} where source_kind is
    'customer', 'group' or 'rrp'. The list holds only variants where the
    customer or the customer's group has set a price — a variant on the
    plain recommended retail price is not listed.
    """
    conditions = Q(pricing_variants__customers=customer)
    if customer.group_id is not None:
        conditions |= Q(group_pricing_variants__customer_group_id=customer.group_id)

    variants = (
        ProductVariant.objects
        .filter(conditions)
        .select_related('product', 'size')
        .prefetch_related('pricing_variants__customers', 'group_pricing_variants')
        .distinct()
        .order_by('product__name', 'code')
    )

    rows = []
    for variant in variants:
        price, source = resolve_price(variant, customer)
        if isinstance(source, GroupPricingVariant):
            source_kind = 'group'
        elif source is not None:
            source_kind = 'customer'
        else:
            source_kind = 'rrp'
        rows.append({'variant': variant, 'price': price, 'source_kind': source_kind})
    return rows


@staff_member_required
def customer_dashboard(request):
    """The whole page. ?view= picks the customers list or the groups list."""
    view = request.GET.get('view', DEFAULT_VIEW)
    if view not in dict(VIEWS):
        view = DEFAULT_VIEW
    search = request.GET.get('q', '').strip()

    context = {
        'views': VIEWS,
        'active_view': view,
        'search': search,
        'all_groups': CustomerGroup.objects.order_by('name'),
    }

    if view == 'groups':
        group = _selected_group(request.GET.get('group', ''))
        context['group_rows'] = _search_groups(search)
        context['group'] = group
        if group is not None:
            context['members'] = group.customers.select_related('user').order_by('businessName')
            context['group_prices'] = (
                group.pricing_variants
                .select_related('product_variant__product', 'product_variant__size')
                .all()
            )
    else:
        customer = _selected_customer(request.GET.get('customer', ''))
        context['customer_rows'] = _search_customers(search)
        context['customer'] = customer
        if customer is not None:
            context['details_form'] = CustomerDetailsForm(instance=customer)
            context['contact_formset'] = ContactFormSet(instance=customer)
            context['resolved_prices'] = _resolved_prices(customer)

    return TemplateResponse(request, 'chemsapp/customer_dashboard.html', context)


@staff_member_required
def customer_list(request):
    """The rows of the customers list, for the live search box."""
    search = request.GET.get('q', '').strip()
    customer = _selected_customer(request.GET.get('customer', ''))
    return TemplateResponse(request, 'chemsapp/_customer_list.html', {
        'customer_rows': _search_customers(search),
        'customer': customer,
        'search': search,
    })


@staff_member_required
def group_list(request):
    """The rows of the groups list, for the live search box."""
    search = request.GET.get('q', '').strip()
    group = _selected_group(request.GET.get('group', ''))
    return TemplateResponse(request, 'chemsapp/_group_list.html', {
        'group_rows': _search_groups(search),
        'group': group,
        'search': search,
    })


@staff_member_required
def save_customer_details(request, customer_id):
    """Save the customer's own fields."""
    customer = get_object_or_404(Customer, pk=customer_id)
    if request.method != 'POST':
        return redirect(_dashboard_url('customers', customer_id=customer.pk))

    form = CustomerDetailsForm(request.POST, instance=customer)
    if form.is_valid():
        form.save()
        messages.success(request, f'Saved the details of {customer.businessName}.')
    else:
        messages.error(request, f'The details did not save: {form.errors.as_text()}')
    return redirect(_dashboard_url('customers', customer_id=customer.pk))


@staff_member_required
def save_customer_contacts(request, customer_id):
    """Save the contact rows of one customer."""
    customer = get_object_or_404(Customer, pk=customer_id)
    if request.method != 'POST':
        return redirect(_dashboard_url('customers', customer_id=customer.pk))

    formset = ContactFormSet(request.POST, instance=customer)
    if formset.is_valid():
        formset.save()
        messages.success(request, f'Saved the contacts of {customer.businessName}.')
    else:
        messages.error(request, f'The contacts did not save: {formset.errors}')
    return redirect(_dashboard_url('customers', customer_id=customer.pk))


@staff_member_required
def set_customer_group(request, customer_id):
    """Set or clear the group of one customer, from the customer editor."""
    customer = get_object_or_404(Customer, pk=customer_id)
    if request.method != 'POST':
        return redirect(_dashboard_url('customers', customer_id=customer.pk))

    group_id = request.POST.get('group', '').strip()
    if group_id:
        group = get_object_or_404(CustomerGroup, pk=group_id)
        customer.group = group
        customer.save(update_fields=['group'])
        messages.success(request, f'Put {customer.businessName} in {group.name}.')
    else:
        customer.group = None
        customer.save(update_fields=['group'])
        messages.success(request, f'Took {customer.businessName} out of its group.')
    return redirect(_dashboard_url('customers', customer_id=customer.pk))


@staff_member_required
def create_group(request):
    """Make a new group, then open it."""
    if request.method != 'POST':
        return redirect(_dashboard_url('groups'))

    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Type a name for the group.')
        return redirect(_dashboard_url('groups'))
    if CustomerGroup.objects.filter(name__iexact=name).exists():
        messages.error(request, f'A group named "{name}" already exists.')
        return redirect(_dashboard_url('groups'))

    group = CustomerGroup.objects.create(name=name)
    messages.success(request, f'Made the group {group.name}.')
    return redirect(_dashboard_url('groups', group_id=group.pk))


@staff_member_required
def rename_group(request, group_id):
    """Change a group's name or note."""
    group = get_object_or_404(CustomerGroup, pk=group_id)
    if request.method != 'POST':
        return redirect(_dashboard_url('groups', group_id=group.pk))

    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'The group needs a name.')
        return redirect(_dashboard_url('groups', group_id=group.pk))
    clash = CustomerGroup.objects.filter(name__iexact=name).exclude(pk=group.pk)
    if clash.exists():
        messages.error(request, f'A group named "{name}" already exists.')
        return redirect(_dashboard_url('groups', group_id=group.pk))

    group.name = name
    group.note = request.POST.get('note', '').strip()
    group.save(update_fields=['name', 'note'])
    messages.success(request, 'Saved the group.')
    return redirect(_dashboard_url('groups', group_id=group.pk))


@staff_member_required
def delete_group(request, group_id):
    """Delete a group. Its customers stay and lose the group (SET_NULL)."""
    group = get_object_or_404(CustomerGroup, pk=group_id)
    if request.method == 'POST':
        name = group.name
        group.delete()
        messages.success(request, f'Deleted the group {name}. Its customers kept.')
    return redirect(_dashboard_url('groups'))


@staff_member_required
def add_group_customers(request, group_id):
    """Put many customers in one group at once, from the search-and-add box."""
    group = get_object_or_404(CustomerGroup, pk=group_id)
    if request.method != 'POST':
        return redirect(_dashboard_url('groups', group_id=group.pk))

    customer_ids = request.POST.getlist('customer')
    customers = Customer.objects.filter(pk__in=customer_ids)
    if not customers:
        messages.error(request, 'Select a customer first.')
        return redirect(_dashboard_url('groups', group_id=group.pk))

    # A ForeignKey holds one value, so this move is safe for a customer that
    # is already in another group: the row is overwritten, not duplicated.
    moved = customers.exclude(group=group).count()
    customers.update(group=group)
    messages.success(request, f'Added {moved} customer(s) to {group.name}.')
    return redirect(_dashboard_url('groups', group_id=group.pk))


@staff_member_required
def remove_group_customer(request, group_id, customer_id):
    """Take one customer out of a group."""
    group = get_object_or_404(CustomerGroup, pk=group_id)
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=customer_id, group=group)
        customer.group = None
        customer.save(update_fields=['group'])
        messages.success(
            request, f'Took {customer.businessName} out of {group.name}.')
    return redirect(_dashboard_url('groups', group_id=group.pk))


@staff_member_required
def group_customer_search(request):
    """Customers matching ?q=, for the "add customers" box on the groups view.

    ?exclude_group=<id> leaves out customers already in that group. The box
    is for adding customers that are not in the group yet, so offering the
    ones that are would only be noise.
    """
    search = request.GET.get('q', '').strip()
    customers = Customer.objects.select_related('user', 'group')

    exclude_group = request.GET.get('exclude_group', '')
    if exclude_group:
        customers = customers.exclude(group_id=exclude_group)

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
         'detail': customer.group.name if customer.group else customer.user.email}
        for customer in customers
    ]
    return JsonResponse({'results': results})


@staff_member_required
def variant_search(request):
    """Product variants matching ?q=, for the "add a group price" box.

    ?exclude_group_priced=<group id> leaves out variants that group already
    has a price for. That group cannot get a second price for the same
    variant, so offering those would only produce an error.
    """
    search = request.GET.get('q', '').strip()
    variants = ProductVariant.objects.select_related('product', 'size')

    exclude_group_priced = request.GET.get('exclude_group_priced', '')
    if exclude_group_priced:
        variants = variants.exclude(
            group_pricing_variants__customer_group_id=exclude_group_priced)

    if search:
        variants = variants.filter(
            Q(code__icontains=search) |
            Q(barcode__icontains=search) |
            Q(product__name__icontains=search) |
            Q(size__name__icontains=search)
        )

    variants = variants.order_by('product__name', 'code')[:SEARCH_LIMIT]
    results = [
        {'id': variant.pk,
         'name': variant.code or str(variant),
         'detail': '{}{}'.format(
             variant.product.name,
             f' · {variant.size}' if variant.size else '')}
        for variant in variants
    ]
    return JsonResponse({'results': results})


@staff_member_required
def add_group_price(request, group_id):
    """Add one price for a group, from the group editor.

    The picker allows more than one variant before saving, so this reads
    every chosen variant and gives each the same price. A variant the group
    already has a price for is skipped, not overwritten.
    """
    group = get_object_or_404(CustomerGroup, pk=group_id)
    if request.method != 'POST':
        return redirect(_dashboard_url('groups', group_id=group.pk))

    variant_ids = request.POST.getlist('variant')
    variants = ProductVariant.objects.filter(pk__in=variant_ids)
    if not variants:
        messages.error(request, 'Select a variant first.')
        return redirect(_dashboard_url('groups', group_id=group.pk))

    try:
        price = Decimal(request.POST.get('price', '').strip())
        if price <= 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        messages.error(request, 'Type a price greater than zero.')
        return redirect(_dashboard_url('groups', group_id=group.pk))

    name = request.POST.get('name', '').strip()
    min_quantity = request.POST.get('min_quantity', '').strip() or None

    already_priced = set(
        GroupPricingVariant.objects
        .filter(customer_group=group, product_variant__in=variants)
        .values_list('product_variant_id', flat=True)
    )
    added = 0
    for variant in variants:
        if variant.pk in already_priced:
            continue
        GroupPricingVariant.objects.create(
            product_variant=variant, customer_group=group, price=price,
            name=name, min_quantity=min_quantity)
        added += 1

    skipped = len(variants) - added
    message = f'Added {added} group price(s) to {group.name}.'
    if skipped:
        message += f' {skipped} variant(s) already had a price and were left alone.'
    messages.success(request, message)
    return redirect(_dashboard_url('groups', group_id=group.pk))


@staff_member_required
def remove_group_price(request, group_id, group_pricing_variant_id):
    """Remove one group price from the group editor."""
    group = get_object_or_404(CustomerGroup, pk=group_id)
    if request.method == 'POST':
        group_price = get_object_or_404(
            GroupPricingVariant, pk=group_pricing_variant_id, customer_group=group)
        group_price.delete()
        messages.success(request, 'Removed the group price.')
    return redirect(_dashboard_url('groups', group_id=group.pk))
