from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.conf import settings
from postmarker.core import PostmarkClient

from chemsapp.models import Customer, ProductVariant
from chemsapp.serializers import CustomerProductVariantSerializer
from .models import CustomerOrder, OrderLineItem
from .serializers import CustomerOrderSerializer, CustomerOrderCreateSerializer
from .utils import OrderPDFGenerator


@api_view(['GET'])
def orders_by_customer(request, customer_id):
    """List all orders for a given customer."""
    profile_type = request.user.profile.profileType

    try:
        if profile_type == 'admin':
            customer = Customer.objects.get(pk=customer_id)
        elif profile_type == 'distributor':
            customer = request.user.profile.distributor.customers.get(pk=customer_id)
        elif profile_type == 'customer':
            customer = request.user.profile.customer
            if customer.pk != int(customer_id):
                return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
    except Customer.DoesNotExist:
        return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

    orders = CustomerOrder.objects.filter(customer=customer).prefetch_related(
        'line_items__product_variant__size',
        'line_items__product_variant__product',
    ).order_by('-created_at')

    serializer = CustomerOrderSerializer(orders, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def submit_order(request):
    """
    Create and submit a CustomerOrder with line items, then generate the PDF.

    Expected payload:
    {
        "customer_id": 1,
        "notes": "...",          # optional
        "line_items": [
            {"product_variant_id": 3, "quantity": 2},
            ...
        ]
    }
    """
    profile_type = request.user.profile.profileType

    input_serializer = CustomerOrderCreateSerializer(data=request.data)
    print(request.data)
    if not input_serializer.is_valid():
        print(input_serializer.errors)
        return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = input_serializer.validated_data
    customer_id = data['customer_id']

    # Permission check
    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

    line_items_data = data.get('line_items', [])
    if not line_items_data:
        return Response({'detail': 'Order must have at least one line item.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate all product variant IDs up front
    variant_ids = [item['product_variant_id'] for item in line_items_data]
    variants = {v.pk: v for v in ProductVariant.objects.filter(pk__in=variant_ids)}
    missing = set(variant_ids) - set(variants.keys())
    if missing:
        return Response(
            {'detail': f'Product variant(s) not found: {sorted(missing)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        order = CustomerOrder.objects.create(
            customer=customer,
            notes=data.get('notes', ''),
            submitted=True,
        )
        OrderLineItem.objects.bulk_create([
            OrderLineItem(
                order=order,
                product_variant=variants[item['product_variant_id']],
                quantity=item['quantity'],
            )
            for item in line_items_data
        ])

    # Generate PDF outside the transaction so a PDF failure doesn't roll back the order
    OrderPDFGenerator(order).generate_and_save()

    # Re-fetch to pick up the pdf field set by generate_and_save()
    order.refresh_from_db()

    serializer = CustomerOrderSerializer(order, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def customer_product_variants(request, customer_id):
    """Return all CustomerProductVariants (with nested variant + size) for a customer."""
    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

    product_variants = customer.product_variants.select_related(
        'product_variant__size',
        'product_variant__product',
    ).order_by('product_variant__description')

    serializer = CustomerProductVariantSerializer(product_variants, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def email_order_pdf(request):
    """
    Generate and email an order PDF.

    POST /orders/email-pdf/

    Expected JSON:
    {
        "email_address": "user@example.com",
        "order_id": 123
    }
    """
    email_address = request.data.get('email_address')
    order_id = request.data.get('order_id')

    if not email_address:
        return Response({'success': False, 'error': 'email_address is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not order_id:
        return Response({'success': False, 'error': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        order = CustomerOrder.objects.get(pk=order_id)
    except CustomerOrder.DoesNotExist:
        return Response({'success': False, 'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Generate PDF if not already present
        if not order.pdf:
            OrderPDFGenerator(order).generate_and_save()
            order.refresh_from_db()

        if not order.pdf:
            return Response({'success': False, 'error': 'Failed to generate PDF'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        order.pdf.open('rb')
        pdf_content = order.pdf.read()
        order.pdf.close()

        postmark = PostmarkClient(server_token=settings.POSTMARK_SERVER_API_TOKEN)
        email = postmark.emails.Email(
            From='noreply@geller.co.nz',
            To=email_address,
            Subject=f'Order {order.order_number} — {order.customer.businessName}',
            HtmlBody=f'''
                <html>
                <body>
                    <h2>Your Order PDF</h2>
                    <p>Please find attached your order:</p>
                    <ul>
                        <li><strong>Order Number:</strong> {order.order_number}</li>
                        <li><strong>Customer:</strong> {order.customer.businessName}</li>
                        <li><strong>Date:</strong> {order.date.strftime("%Y-%m-%d")}</li>
                        <li><strong>Status:</strong> {order.get_fulfilment_status_display()}</li>
                    </ul>
                </body>
                </html>
            ''',
            TextBody=f'Order Number: {order.order_number}\nCustomer: {order.customer.businessName}\nDate: {order.date.strftime("%Y-%m-%d")}\nStatus: {order.get_fulfilment_status_display()}',
        )
        email.attach_binary(content=pdf_content, filename=f'order-{order.order_number}.pdf')
        email.send()

        return Response({
            'success': True,
            'message': f'Order PDF sent to {email_address}',
            'order': {
                'order_number': order.order_number,
                'customer': order.customer.businessName,
                'date': order.date.strftime('%Y-%m-%d'),
                'status': order.get_fulfilment_status_display(),
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
