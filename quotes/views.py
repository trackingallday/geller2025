from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from chemsapp.models import Customer, ProductVariant
from .models import Quote
from .serializers import QuoteCatalogueVariantSerializer, QuoteCreateSerializer, QuoteSerializer
from .services import create_quote, send_quote_pdf_email


@api_view(['GET'])
def quote_catalogue(request):
    """Full product-variant catalogue for the quote builder (not customer-filtered)."""
    variants = ProductVariant.objects.select_related('product', 'size').prefetch_related(
        'product__fill_types',
        'fill_overrides__fill_type',
    ).order_by('product__name', 'code')
    serializer = QuoteCatalogueVariantSerializer(variants, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def submit_quote(request):
    """
    Create a quote with priced lines, snapshot cost-in-use, and generate the PDF.

    Expected payload:
    {
        "company_name": "XYZ CAFE",
        "address": "29 BRIDGE ST\nCAMBRIDGE",     # optional
        "contact_name": "Sam Brown",              # optional
        "customer_id": 7,                         # optional prefill provenance
        "lines": [
            {"product_variant_id": 12, "price": "89.90"},
            ...
        ]
    }
    """
    input_serializer = QuoteCreateSerializer(data=request.data)
    if not input_serializer.is_valid():
        return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = input_serializer.validated_data

    lines_data = data.get('lines', [])
    if not lines_data:
        return Response({'detail': 'Quote must have at least one line.'}, status=status.HTTP_400_BAD_REQUEST)

    customer = None
    customer_id = data.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Validate all product variant IDs up front
    variant_ids = [line['product_variant_id'] for line in lines_data]
    variants = {
        v.pk: v for v in ProductVariant.objects.filter(pk__in=variant_ids).select_related('product').prefetch_related(
            'product__fill_types', 'fill_overrides__fill_type',
        )
    }
    missing = set(variant_ids) - set(variants.keys())
    if missing:
        return Response(
            {'detail': f'Product variant(s) not found: {sorted(missing)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    quote = create_quote(
        user=request.user,
        company_name=data['company_name'],
        address=data.get('address', ''),
        contact_name=data.get('contact_name', ''),
        customer=customer,
        lines=[
            {'variant': variants[line['product_variant_id']], 'price': line['price']}
            for line in lines_data
        ],
    )

    serializer = QuoteSerializer(quote, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def quotes_list(request):
    """List quotes, newest first. ?mine=1 filters to the requesting user's."""
    quotes = Quote.objects.prefetch_related('lines').order_by('-created_at')
    if request.query_params.get('mine'):
        quotes = quotes.filter(created_by=request.user)
    serializer = QuoteSerializer(quotes, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def quote_detail(request, pk):
    try:
        quote = Quote.objects.prefetch_related('lines').get(pk=pk)
    except Quote.DoesNotExist:
        return Response({'detail': 'Quote not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = QuoteSerializer(quote, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def email_quote_pdf(request):
    """
    Generate and email a proposal PDF.

    POST /quotes/email-pdf/
    Expected JSON: {"email_address": "user@example.com", "quote_id": 123}
    """
    email_address = request.data.get('email_address')
    quote_id = request.data.get('quote_id')

    if not email_address:
        return Response({'success': False, 'error': 'email_address is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not quote_id:
        return Response({'success': False, 'error': 'quote_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        quote = Quote.objects.get(pk=quote_id)
    except Quote.DoesNotExist:
        return Response({'success': False, 'error': 'Quote not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        send_quote_pdf_email(quote, email_address)
        return Response({
            'success': True,
            'message': f'Proposal PDF sent to {email_address}',
            'quote': {
                'quote_number': quote.quote_number,
                'company_name': quote.company_name,
                'date': quote.date.strftime('%Y-%m-%d'),
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
