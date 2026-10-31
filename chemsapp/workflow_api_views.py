"""JSON reads for the orders, proposals and tickets screens.

These three are list-and-detail screens over models the Django admin and
three separate dashboards each present differently. One module, because
they share a shape: a filtered list, one record with its children, and in
two cases a PDF to stream.
"""
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from orders.models import CustomerOrder
from quotes.models import Quote
from tickets.models import Ticket

from .staff_api import ok, staff_api

PAGE_SIZE = 50


def _money(value):
    return None if value is None else str(value)


def _when(value):
    return value.isoformat() if value else None


def _file(field):
    if not field:
        return None
    try:
        return {'name': field.name.rsplit('/', 1)[-1], 'url': field.url}
    except ValueError:
        return None


def _page(queryset, request):
    """One page of rows, with the counts a pager needs."""
    total = queryset.count()
    try:
        page = max(1, int(request.GET.get('page', '1')))
    except ValueError:
        page = 1
    start = (page - 1) * PAGE_SIZE
    return queryset[start:start + PAGE_SIZE], {
        'total': total,
        'page': page,
        'page_size': PAGE_SIZE,
        'has_more': start + PAGE_SIZE < total,
    }


# --- Orders -----------------------------------------------------------------

def _order_row(order):
    return {
        'id': order.pk,
        'order_number': order.order_number,
        'customer': (
            {'id': order.customer_id, 'name': order.customer.businessName}
            if order.customer_id else None
        ),
        'date': _when(order.date),
        'fulfilment_status': order.fulfilment_status,
        'submitted': order.submitted,
        'pdf': _file(order.pdf),
        'created_at': _when(order.created_at),
    }


@staff_api
def order_list(request):
    orders = CustomerOrder.objects.select_related('customer')

    search = request.GET.get('q', '').strip()
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search)
            | Q(customer__businessName__icontains=search))

    status = request.GET.get('status', '').strip()
    if status:
        orders = orders.filter(fulfilment_status=status)

    submitted = request.GET.get('submitted', '')
    if submitted in ('0', '1'):
        orders = orders.filter(submitted=submitted == '1')

    customer = request.GET.get('customer', '').strip()
    if customer.isdigit():
        orders = orders.filter(customer_id=int(customer))

    rows, meta = _page(orders.order_by('-created_at'), request)
    return ok({'orders': [_order_row(o) for o in rows], **meta})


@staff_api
def order_detail(request, order_id):
    order = get_object_or_404(
        CustomerOrder.objects
        .select_related('customer')
        .prefetch_related('line_items__product_variant__product',
                          'line_items__product_variant__size'),
        pk=order_id,
    )

    return ok({
        **_order_row(order),
        'notes': order.notes,
        'line_items': [
            {
                'id': item.pk,
                'quantity': item.quantity,
                'soh': item.soh,
                'max_stock_level': item.max_stock_level,
                'variant': {
                    'id': item.product_variant_id,
                    'code': item.product_variant.code,
                    'size': (
                        item.product_variant.size.name
                        if item.product_variant.size_id else None
                    ),
                    'product': {
                        'id': item.product_variant.product_id,
                        'name': item.product_variant.product.name,
                    },
                } if item.product_variant_id else None,
            }
            for item in order.line_items.all()
        ],
    })


# --- Proposals (quotes) ------------------------------------------------------

def _quote_row(quote):
    return {
        'id': quote.pk,
        'quote_number': quote.quote_number,
        'company_name': quote.company_name,
        'contact_name': quote.contact_name,
        'customer': (
            {'id': quote.customer_id, 'name': quote.customer.businessName}
            if quote.customer_id else None
        ),
        'created_by': quote.created_by.username if quote.created_by_id else None,
        'date': _when(quote.date),
        'pdf': _file(quote.pdf),
        'created_at': _when(quote.created_at),
    }


@staff_api
def quote_list(request):
    quotes = Quote.objects.select_related('customer', 'created_by')

    search = request.GET.get('q', '').strip()
    if search:
        quotes = quotes.filter(
            Q(quote_number__icontains=search)
            | Q(company_name__icontains=search)
            | Q(contact_name__icontains=search)
            | Q(customer__businessName__icontains=search))

    customer = request.GET.get('customer', '').strip()
    if customer.isdigit():
        quotes = quotes.filter(customer_id=int(customer))

    rows, meta = _page(quotes.order_by('-created_at'), request)
    return ok({'quotes': [_quote_row(q) for q in rows], **meta})


@staff_api
def quote_detail(request, quote_id):
    """One proposal and its lines.

    A line keeps a frozen copy of the product's name, code and cost-in-use
    from when the proposal was made, so what is shown here is what the
    customer was sent, not what the catalogue says today.
    """
    quote = get_object_or_404(
        Quote.objects
        .select_related('customer', 'created_by')
        .prefetch_related('lines__product_variant__size', 'lines__dilutions'),
        pk=quote_id,
    )

    return ok({
        **_quote_row(quote),
        'address': quote.address,
        'lines': [
            {
                'id': line.pk,
                'price': _money(line.price),
                'product_name': line.product_name,
                'product_subheading': line.product_subheading,
                'product_code': line.product_code,
                'description': line.description,
                'row_color': line.row_color,
                'cost_in_use': line.cost_in_use,
                'variant': {
                    'id': line.product_variant_id,
                    'code': line.product_variant.code,
                    'size': (
                        line.product_variant.size.name
                        if line.product_variant.size_id else None
                    ),
                } if line.product_variant_id else None,
            }
            for line in quote.lines.all()
        ],
    })


# --- Tickets -----------------------------------------------------------------

def _ticket_row(ticket):
    return {
        'id': ticket.pk,
        'subject': ticket.subject,
        'status': ticket.status,
        'ticket_type': ticket.ticket_type,
        'customer': (
            {'id': ticket.customer_id, 'name': ticket.customer.businessName}
            if ticket.customer_id else None
        ),
        'created_by': ticket.created_by.username if ticket.created_by_id else None,
        'assigned_to': ticket.assigned_to.username if ticket.assigned_to_id else None,
        'source_report': (
            {'id': ticket.source_report_id,
             'document_number': ticket.source_report.document_number}
            if ticket.source_report_id else None
        ),
        'created_at': _when(ticket.created_at),
        'updated_at': _when(ticket.updated_at),
    }


@staff_api
def ticket_list(request):
    tickets = Ticket.objects.select_related(
        'customer', 'created_by', 'assigned_to', 'source_report')

    search = request.GET.get('q', '').strip()
    if search:
        tickets = tickets.filter(
            Q(subject__icontains=search)
            | Q(body__icontains=search)
            | Q(customer__businessName__icontains=search))

    status = request.GET.get('status', '').strip()
    if status:
        tickets = tickets.filter(status=status)

    ticket_type = request.GET.get('type', '').strip()
    if ticket_type:
        tickets = tickets.filter(ticket_type=ticket_type)

    assigned = request.GET.get('assigned_to', '').strip()
    if assigned.isdigit():
        tickets = tickets.filter(assigned_to_id=int(assigned))

    customer = request.GET.get('customer', '').strip()
    if customer.isdigit():
        tickets = tickets.filter(customer_id=int(customer))

    rows, meta = _page(tickets.order_by('-updated_at'), request)
    return ok({'tickets': [_ticket_row(t) for t in rows], **meta})


@staff_api
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(
        Ticket.objects
        .select_related('customer', 'created_by', 'assigned_to', 'source_report')
        .prefetch_related('replies__author', 'images'),
        pk=ticket_id,
    )

    return ok({
        **_ticket_row(ticket),
        'body': ticket.body,
        'replies': [
            {
                'id': reply.pk,
                'author': reply.author.username if reply.author_id else None,
                'body': reply.body,
                'created_at': _when(reply.created_at),
            }
            for reply in ticket.replies.all()
        ],
        'images': [
            {
                'id': image.pk,
                'file': _file(image.image),
                'uploaded_by': (
                    image.uploaded_by.username if image.uploaded_by_id else None),
                'uploaded_at': _when(image.uploaded_at),
            }
            for image in ticket.images.all()
        ],
    })


# --- Shared ------------------------------------------------------------------

def _stream_pdf(field, filename):
    if not field:
        raise Http404('There is no PDF for this record yet.')
    return FileResponse(
        field.open('rb'), content_type='application/pdf', filename=filename)


@staff_api
def order_pdf(request, order_id):
    """The order's PDF, behind the staff gate rather than linked directly."""
    order = get_object_or_404(CustomerOrder, pk=order_id)
    return _stream_pdf(order.pdf, f'{order.order_number or order.pk}.pdf')


@staff_api
def quote_pdf(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    return _stream_pdf(quote.pdf, f'{quote.quote_number or quote.pk}.pdf')
