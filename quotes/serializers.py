from decimal import Decimal

from rest_framework import serializers

from chemsapp.models import ProductVariant
from .models import Quote, QuoteLine


class QuoteLineSerializer(serializers.ModelSerializer):
    product_variant_id = serializers.PrimaryKeyRelatedField(source='product_variant', read_only=True)

    class Meta:
        model = QuoteLine
        fields = (
            'id', 'product_variant_id', 'price', 'sort_order',
            'product_name', 'product_subheading', 'product_code', 'description', 'cost_in_use',
        )


class QuoteSerializer(serializers.ModelSerializer):
    lines = QuoteLineSerializer(many=True, read_only=True)
    pdf_url = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = (
            'id', 'quote_number', 'company_name', 'address', 'contact_name',
            'customer', 'created_by_name', 'date', 'pdf_url', 'lines',
            'created_at', 'updated_at',
        )

    def get_pdf_url(self, obj):
        if obj.pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf.url)
            return obj.pdf.url
        return None

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class QuoteLineWriteSerializer(serializers.Serializer):
    product_variant_id = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))


class QuoteCreateSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    address = serializers.CharField(required=False, allow_blank=True)
    contact_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    lines = QuoteLineWriteSerializer(many=True)


class QuoteCatalogueVariantSerializer(serializers.ModelSerializer):
    """Whole-catalogue picker for the quote builder, with enough data for a
    live client-side cost-in-use preview (price ÷ fills)."""
    product_id = serializers.PrimaryKeyRelatedField(source='product', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    subheading = serializers.CharField(source='product.subheading', read_only=True)
    dilution_ratio = serializers.DecimalField(
        source='product.dilution_ratio', max_digits=8, decimal_places=2, read_only=True)
    size_name = serializers.CharField(source='size.name', read_only=True, default=None)
    image_url = serializers.SerializerMethodField()
    fill_options = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = (
            'id', 'code', 'barcode', 'pack_size', 'description', 'volume_litres',
            'product_id', 'product_name', 'subheading', 'dilution_ratio',
            'size_name', 'image_url', 'fill_options',
        )

    def get_image_url(self, obj):
        image = obj.image or obj.product.primaryImageLink
        if not image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(image.url)
        return image.url

    def get_fill_options(self, obj):
        return [
            {
                'fill_type_id': option['fill_type'].id,
                'fill_type': option['fill_type'].name,
                'fills': str(option['fills']),
                'source': option['source'],
            }
            for option in obj.get_fill_options()
        ]
