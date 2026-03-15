from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from chemsapp.models import Customer
from .models import Ticket, TicketReply, TicketImage
from .serializers import TicketSerializer, TicketCreateSerializer


@api_view(['GET'])
def ticket_list(request):
    """List tickets with optional filters: ?status=, ?customer=, ?assigned_to="""
    tickets = Ticket.objects.select_related('created_by', 'assigned_to', 'customer').prefetch_related(
        'replies__author', 'images',
    ).order_by('-created_at')

    filter_status = request.query_params.get('status')
    filter_customer = request.query_params.get('customer')
    filter_assigned_to = request.query_params.get('assigned_to')

    if filter_status:
        tickets = tickets.filter(status=filter_status)
    if filter_customer:
        tickets = tickets.filter(customer_id=filter_customer)
    if filter_assigned_to:
        tickets = tickets.filter(assigned_to_id=filter_assigned_to)

    serializer = TicketSerializer(tickets, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def ticket_create(request):
    """Create a new ticket. created_by is set to request.user."""
    input_serializer = TicketCreateSerializer(data=request.data)
    if not input_serializer.is_valid():
        return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = input_serializer.validated_data

    try:
        customer = Customer.objects.get(pk=data['customer_id'])
    except Customer.DoesNotExist:
        return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

    ticket = Ticket.objects.create(
        created_by=request.user,
        customer=customer,
        subject=data['subject'],
        body=data['body'],
    )

    serializer = TicketSerializer(ticket, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def ticket_detail(request, ticket_id):
    """Retrieve a single ticket with replies and images."""
    try:
        ticket = Ticket.objects.select_related('created_by', 'assigned_to', 'customer').prefetch_related(
            'replies__author', 'images',
        ).get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return Response({'detail': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = TicketSerializer(ticket, context={'request': request})
    return Response(serializer.data)


@api_view(['PATCH'])
def ticket_update(request, ticket_id):
    """Update ticket status and/or assigned_to_id."""
    try:
        ticket = Ticket.objects.get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return Response({'detail': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)

    if 'status' in request.data:
        ticket.status = request.data['status']
    if 'assigned_to_id' in request.data:
        ticket.assigned_to_id = request.data['assigned_to_id']

    ticket.save()

    serializer = TicketSerializer(ticket, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def ticket_reply(request, ticket_id):
    """Add a reply to a ticket. Only the creator or assignee may reply."""
    try:
        ticket = Ticket.objects.get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return Response({'detail': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.user != ticket.created_by and request.user != ticket.assigned_to:
        return Response({'detail': 'You do not have permission to reply to this ticket.'}, status=status.HTTP_403_FORBIDDEN)

    body = request.data.get('body', '').strip()
    if not body:
        return Response({'detail': 'Reply body is required.'}, status=status.HTTP_400_BAD_REQUEST)

    TicketReply.objects.create(ticket=ticket, author=request.user, body=body)

    ticket.refresh_from_db()
    serializer = TicketSerializer(
        Ticket.objects.prefetch_related('replies__author', 'images').get(pk=ticket_id),
        context={'request': request},
    )
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def ticket_upload_image(request, ticket_id):
    """Upload an image to a ticket."""
    try:
        ticket = Ticket.objects.get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return Response({'detail': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)

    image_file = request.FILES.get('image')
    if not image_file:
        return Response({'detail': 'No image file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    TicketImage.objects.create(ticket=ticket, image=image_file, uploaded_by=request.user)

    ticket_with_data = Ticket.objects.prefetch_related('replies__author', 'images').get(pk=ticket_id)
    serializer = TicketSerializer(ticket_with_data, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)
