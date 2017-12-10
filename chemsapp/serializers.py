from django.contrib.auth.models import User
from chemsapp.models import ProductRemove, ProductAdd, Product, Customer, Distributor, SafetyWear
from rest_framework import serializers


class ProductSerializer(serializers.ModelSerializer):

    customers = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'primaryImageLink', 'secondaryImageLink', 'usageType', 'amountDesc',
            'instructions', 'productCode', 'brand', 'infoSheet', 'sdsSheet',
            'safetyWears', 'customers',
        )


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email',
        )


class CustomerSerializer(serializers.ModelSerializer):

    user = UserSerializer(many=False, read_only=True)
    products = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = (
            'id', 'phoneNumber', 'user', 'cellPhoneNumber', 'businessName',
            'products', 'address', 'geocodingDetail',
        )


class SafetyWearSerializer(serializers.ModelSerializer):

    class Meta:
        model = SafetyWear
        fields = (
            'id', 'name', 'imageLink',
        )

