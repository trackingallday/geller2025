from rest_framework import serializers
from .models import CustomerOrder, OrderLineItem
from chemsapp.models import ProductVariant
from chemsapp.serializers import ProductVariantSerializer


class OrderLineItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(many=False, read_only=True)
    product_variant_id = serializers.PrimaryKeyRelatedField(
        source='product_variant',
        queryset=ProductVariant.objects.all(),
        write_only=True,
    )

    class Meta:
        model = OrderLineItem
        fields = ('id', 'product_variant', 'product_variant_id', 'quantity', 'soh', 'max_stock_level')


class CustomerOrderSerializer(serializers.ModelSerializer):
    line_items = OrderLineItemSerializer(many=True, read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomerOrder
        fields = (
            'id', 'order_number', 'date', 'fulfilment_status',
            'notes', 'submitted', 'pdf_url', 'line_items',
            'created_at', 'updated_at',
        )

    def get_pdf_url(self, obj):
        if obj.pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf.url)
            return obj.pdf.url
        return None


class OrderLineItemWriteSerializer(serializers.Serializer):
    product_variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=0)
    # Optional so older app builds that don't send these still submit successfully.
    soh = serializers.IntegerField(min_value=0, required=False, default=0)
    max_stock_level = serializers.IntegerField(min_value=0, required=False, default=0)


class CustomerOrderCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    line_items = OrderLineItemWriteSerializer(many=True)
