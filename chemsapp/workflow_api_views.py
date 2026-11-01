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

from .models import Customer, ProductVariant
from .staff_api import error, json_body, ok, staff_api

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


@staff_api
def quote_catalogue(request):
    """What the proposal builder picks from: product → variant → dilution,
    and the customers with their address and contacts. The same lists the
    dashboard's builder page embeds, from the same function.
    """
    from quotes.dashboard_views import _builder_context
    return ok(_builder_context())


@staff_api
def quote_price(request):
    """The price to suggest for one line: ?variant=&customer=.

    A suggestion only: the user can always type over it. Through the same
    resolver as every other price, so the builder and the product screen
    agree.
    """
    from chemsapp.pricing import resolve_price
    from quotes.services import describe_price_source

    variant = ProductVariant.objects.filter(pk=_int(request.GET.get('variant'))).first()
    if variant is None:
        return ok({'price': None, 'source': None})
    customer = Customer.objects.filter(pk=_int(request.GET.get('customer'))).first()
    price, pricing = resolve_price(variant, customer)
    return ok({
        'price': _money(price),
        'source': describe_price_source(price, pricing),
    })


def _int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


@staff_api
def quote_create(request):
    """Make a proposal, freeze its lines and build its PDF.

    Body: {company_name, address, contact_name, customer, lines: [{variant,
    price, dilution}]}. The lines go through the same checks as the
    dashboard's builder page.
    """
    from quotes.services import QuoteLineError, build_quote_lines, create_quote

    if request.method != 'POST':
        return error('POST required.', status=405)
    body = json_body(request)
    company_name = str(body.get('company_name') or '').strip()
    try:
        lines = build_quote_lines(body.get('lines') or [])
    except QuoteLineError as e:
        return error(str(e), errors={'lines': [str(e)]})
    if not company_name:
        return error('Company name is required.', errors={'company_name': ['Company name is required.']})
    if not lines:
        return error('Add at least one product line.', errors={'lines': ['Add at least one product line.']})

    quote = create_quote(
        user=request.user,
        company_name=company_name,
        address=str(body.get('address') or '').strip(),
        contact_name=str(body.get('contact_name') or '').strip(),
        customer=Customer.objects.filter(pk=_int(body.get('customer'))).first(),
        lines=lines,
    )
    return ok(_quote_row(quote))


@staff_api
def quote_email(request, quote_id):
    """Email the proposal's PDF to one address, building the PDF if missing."""
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    from quotes.services import send_quote_pdf_email

    if request.method != 'POST':
        return error('POST required.', status=405)
    quote = get_object_or_404(Quote, pk=quote_id)
    address = str(json_body(request).get('email_address') or '').strip()
    try:
        validate_email(address)
    except ValidationError:
        return error('Type a valid email address.', errors={'email_address': ['Type a valid email address.']})
    try:
        send_quote_pdf_email(quote, address)
    except Exception as e:
        return error(f'The email did not send: {e}', status=502)
    return ok({'id': quote.pk, 'email_address': address})


@staff_api
def quote_regenerate_pdf(request, quote_id):
    """Build the proposal's PDF again from its frozen lines."""
    from quotes.utils import QuotePDFGenerator

    if request.method != 'POST':
        return error('POST required.', status=405)
    quote = get_object_or_404(Quote, pk=quote_id)
    QuotePDFGenerator(quote).generate_and_save()
    quote.refresh_from_db()
    return ok(_quote_row(quote))


@staff_api
def quote_delete(request, quote_id):
    if request.method != 'POST':
        return error('POST required.', status=405)
    quote = get_object_or_404(Quote, pk=quote_id)
    number = quote.quote_number
    quote.delete()
    return ok({'id': quote_id, 'quote_number': number})


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

    # A distributor's tickets are those of the customers it serves.
    distributor = request.GET.get('distributor', '').strip()
    if distributor.isdigit():
        tickets = tickets.filter(customer__distributors__id=int(distributor)).distinct()

    rows, meta = _page(tickets.order_by('-updated_at'), request)
    return ok({'tickets': [_ticket_row(t) for t in rows], **meta})


def _ticket_detail(ticket_id, user):
    ticket = get_object_or_404(
        Ticket.objects
        .select_related('customer', 'created_by', 'assigned_to', 'source_report')
        .prefetch_related('replies__author', 'images'),
        pk=ticket_id,
    )
    return {
        **_ticket_row(ticket),
        'body': ticket.body,
        'replies': [
            {
                'id': reply.pk,
                'author': reply.author.username if reply.author_id else None,
                'body': reply.body,
                'created_at': _when(reply.created_at),
                # The thread shows the reader's own replies on the right.
                'is_self': reply.author_id == user.pk,
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
    }


@staff_api
def ticket_detail(request, ticket_id):
    return ok(_ticket_detail(ticket_id, request.user))


def _bump(ticket):
    """New activity on a ticket marked read puts it back to pending, and
    every save moves it to the top of the list, as the old dashboard did."""
    if ticket.status == 'read':
        ticket.status = 'pending'
    ticket.save()


@staff_api
def ticket_create(request):
    """Body: {customer, subject, body, assigned_to}. Assigning is optional."""
    from django.contrib.auth.models import User

    if request.method != 'POST':
        return error('POST required.', status=405)
    body = json_body(request)
    errors = {}
    customer = Customer.objects.filter(pk=_int(body.get('customer'))).first()
    if customer is None:
        errors['customer'] = ['Choose a customer.']
    subject = str(body.get('subject') or '').strip()
    if not subject:
        errors['subject'] = ['Type a subject.']
    text = str(body.get('body') or '').strip()
    if not text:
        errors['body'] = ['Say what the ticket is about.']
    assignee = None
    if body.get('assigned_to'):
        assignee = User.objects.filter(pk=_int(body.get('assigned_to'))).first()
        if assignee is None:
            errors['assigned_to'] = ['That person does not exist.']
    if errors:
        return error('The ticket was not made.', errors=errors)

    ticket = Ticket.objects.create(
        created_by=request.user, customer=customer, subject=subject, body=text,
        assigned_to=assignee)
    return ok(_ticket_detail(ticket.pk, request.user))


@staff_api
def ticket_update(request, ticket_id):
    """Body: {status} and/or {assigned_to}. `assigned_to: null` unassigns.

    Only the model's own statuses are taken; the old dashboard saved
    whatever it was sent.
    """
    from django.contrib.auth.models import User
    from tickets.models import TICKET_STATUS_CHOICES

    if request.method != 'POST':
        return error('POST required.', status=405)
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    body = json_body(request)
    if 'status' in body:
        status = str(body.get('status') or '')
        if status not in dict(TICKET_STATUS_CHOICES):
            return error('That is not a ticket status.', errors={'status': ['That is not a ticket status.']})
        ticket.status = status
    if 'assigned_to' in body:
        if body['assigned_to'] in (None, ''):
            ticket.assigned_to = None
        else:
            assignee = User.objects.filter(pk=_int(body['assigned_to'])).first()
            if assignee is None:
                return error('That person does not exist.', errors={'assigned_to': ['That person does not exist.']})
            ticket.assigned_to = assignee
    ticket.save()
    return ok(_ticket_detail(ticket.pk, request.user))


@staff_api
def ticket_reply(request, ticket_id):
    from tickets.models import TicketReply

    if request.method != 'POST':
        return error('POST required.', status=405)
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    text = str(json_body(request).get('body') or '').strip()
    if not text:
        return error('Type a reply.', errors={'body': ['Type a reply.']})
    TicketReply.objects.create(ticket=ticket, author=request.user, body=text)
    _bump(ticket)
    return ok(_ticket_detail(ticket.pk, request.user))


@staff_api
def ticket_image(request, ticket_id):
    """Attach a photo. It is shrunk in the background, as the old dashboard
    did, so a phone's full-size picture does not fill the disk."""
    import threading

    from chemsapp.views import downscale_image
    from tickets.models import TicketImage

    if request.method != 'POST':
        return error('POST required.', status=405)
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    upload = request.FILES.get('image')
    if upload is None:
        return error('Choose an image.', errors={'image': ['Choose an image.']})
    image = TicketImage.objects.create(ticket=ticket, image=upload, uploaded_by=request.user)
    threading.Thread(target=downscale_image, args=(image.image.path,), daemon=True).start()
    _bump(ticket)
    return ok(_ticket_detail(ticket.pk, request.user))


@staff_api
def customer_distributors(request, customer_id):
    """The distributors serving a customer, for the new-ticket form."""
    customer = get_object_or_404(Customer, pk=customer_id)
    return ok({'distributors': [
        {'id': d.pk, 'name': d.businessname}
        for d in customer.distributors.order_by('businessname')
    ]})


@staff_api
def distributor_users(request, distributor_id):
    """The people at a distributor, who a ticket can be assigned to."""
    from django.contrib.auth.models import User

    users = User.objects.filter(distributors__id=distributor_id).order_by('username')
    return ok({'users': [
        {'id': u.pk, 'name': f'{u.get_full_name() or u.username} ({u.username})'}
        for u in users
    ]})


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
