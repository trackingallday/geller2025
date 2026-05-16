import threading

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse

from chemsapp.models import Customer, Distributor
from chemsapp.views import downscale_image
from .models import Ticket, TicketReply, TicketImage


def _build_filter_querystring(params):
    """Build a query string from filter params (excluding 'ticket')."""
    parts = []
    for key in ('status', 'customer', 'distributor', 'assigned_to'):
        val = params.get(key, '')
        if val:
            parts.append(f'{key}={val}')
    return '&'.join(parts)


@login_required
def ticket_dashboard(request):
    status = request.GET.get('status', '')
    customer_id = request.GET.get('customer', '')
    distributor_id = request.GET.get('distributor', '')
    assigned_to = request.GET.get('assigned_to', '')
    active_ticket_id = request.GET.get('ticket', '')

    tickets = (
        Ticket.objects
        .select_related('customer', 'created_by', 'assigned_to')
        .prefetch_related('replies', 'images', 'customer__distributors')
        .order_by('-updated_at')
    )
    if status:
        tickets = tickets.filter(status=status)
    if customer_id:
        tickets = tickets.filter(customer_id=customer_id)
    if distributor_id:
        tickets = tickets.filter(customer__distributors__id=distributor_id)
    if assigned_to:
        tickets = tickets.filter(assigned_to_id=assigned_to)

    active_ticket = None
    if active_ticket_id:
        try:
            active_ticket = (
                Ticket.objects
                .select_related('customer', 'created_by', 'assigned_to')
                .prefetch_related('replies__author', 'images__uploaded_by')
                .get(pk=active_ticket_id)
            )
        except Ticket.DoesNotExist:
            pass

    if distributor_id:
        customers = Customer.objects.filter(distributors__id=distributor_id).order_by('businessName')
    else:
        customers = Customer.objects.all().order_by('businessName')

    filter_querystring = _build_filter_querystring(request.GET)
    filter_params = {
        'status': status,
        'customer': customer_id,
        'distributor': distributor_id,
        'assigned_to': assigned_to,
    }

    context = {
        'tickets': tickets,
        'active_ticket': active_ticket,
        'customers': customers,
        'distributors': Distributor.objects.all().order_by('businessname'),
        'staff_users': User.objects.filter(is_staff=True).order_by('username'),
        'status_choices': [('', 'All Statuses'), ('pending', 'Pending'), ('read', 'Read'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        'filter_querystring': filter_querystring,
        'filter_params': filter_params,
        'current_status': status,
        'current_customer': customer_id,
        'current_distributor': distributor_id,
        'current_assigned_to': assigned_to,
    }
    return TemplateResponse(request, 'tickets/dashboard.html', context)


@login_required
def ajax_distributors_for_customer(request):
    customer_id = request.GET.get('customer_id', '')
    if not customer_id:
        return JsonResponse({'distributors': []})
    distributors = Distributor.objects.filter(customers__id=customer_id).order_by('businessname')
    data = [{'id': d.pk, 'name': d.businessname} for d in distributors]
    return JsonResponse({'distributors': data})


@login_required
def ajax_users_for_distributor(request):
    distributor_id = request.GET.get('distributor_id', '')
    if not distributor_id:
        return JsonResponse({'users': []})
    users = User.objects.filter(distributors__id=distributor_id).order_by('username')
    data = [{'id': u.pk, 'name': f'{u.get_full_name() or u.username} ({u.username})'} for u in users]
    return JsonResponse({'users': data})


@login_required
def dashboard_create_ticket(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        assigned_to_id = request.POST.get('assigned_to_id', '').strip()
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        if customer_id and subject and body:
            ticket = Ticket.objects.create(
                created_by=request.user,
                customer_id=customer_id,
                subject=subject,
                body=body,
                assigned_to_id=assigned_to_id or None,
            )
            qs = _build_filter_querystring(request.POST)
            redirect_url = f'/tickets/dashboard/?ticket={ticket.pk}'
            if qs:
                redirect_url += f'&{qs}'
            return redirect(redirect_url)
    return redirect('/tickets/dashboard/')


@login_required
def dashboard_reply(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            TicketReply.objects.create(ticket=ticket, author=request.user, body=body)
            if ticket.status == 'read':
                ticket.status = 'pending'
            ticket.save()  # update updated_at
    qs = _build_filter_querystring(request.POST)
    redirect_url = f'/tickets/dashboard/?ticket={ticket_id}'
    if qs:
        redirect_url += f'&{qs}'
    return redirect(redirect_url)


@login_required
def dashboard_update_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        assigned_to_id = request.POST.get('assigned_to_id', '').strip()
        if new_status:
            ticket.status = new_status
        if assigned_to_id:
            ticket.assigned_to_id = assigned_to_id
        elif 'assigned_to_id' in request.POST and not assigned_to_id:
            ticket.assigned_to = None
        ticket.save()
    qs = _build_filter_querystring(request.POST)
    redirect_url = f'/tickets/dashboard/?ticket={ticket_id}'
    if qs:
        redirect_url += f'&{qs}'
    return redirect(redirect_url)


@login_required
def ajax_poll_ticket(request, ticket_id):
    """Return replies and images added after ?after_reply=<id>&after_image=<id>."""
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    after_reply = request.GET.get('after_reply', 0)
    after_image = request.GET.get('after_image', 0)

    replies = ticket.replies.select_related('author').filter(pk__gt=after_reply).order_by('pk')
    images = ticket.images.select_related('uploaded_by').filter(pk__gt=after_image).order_by('pk')

    return JsonResponse({
        'replies': [
            {
                'id': r.pk,
                'body': r.body,
                'author': r.author.username,
                'created_at': r.created_at.strftime('%b %-d, %Y %H:%M'),
                'is_self': r.author_id == request.user.pk,
            }
            for r in replies
        ],
        'images': [
            {
                'id': i.pk,
                'url': i.image.url,
                'uploaded_by': i.uploaded_by.username,
                'uploaded_at': i.uploaded_at.strftime('%b %-d, %Y %H:%M'),
            }
            for i in images
        ],
    })


@login_required
def dashboard_upload_image(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.method == 'POST' and request.FILES.get('image'):
        ticket_image = TicketImage.objects.create(
            ticket=ticket,
            image=request.FILES['image'],
            uploaded_by=request.user,
        )
        threading.Thread(target=downscale_image, args=(ticket_image.image.path,), daemon=True).start()
        if ticket.status == 'read':
            ticket.status = 'pending'
        ticket.save()  # update updated_at
    qs = _build_filter_querystring(request.POST)
    redirect_url = f'/tickets/dashboard/?ticket={ticket_id}'
    if qs:
        redirect_url += f'&{qs}'
    return redirect(redirect_url)
