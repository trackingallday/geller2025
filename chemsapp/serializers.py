from django.contrib.auth.models import User
from chemsapp.models import ProductRemove, ProductAdd, Product, Customer, Distributor
from rest_framework import serializers


class ProductSerializer(serializers.ModelSerializer):

    customers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            'name', 'primaryImageLink', 'secondaryImageLink', 'usageType', 'amountDesc',
            'instructions', 'productCode', 'brand', 'infoSheetLink', 'sdsSheetLink',
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
            'phoneNumber', 'user', 'cellPhoneNumber', 'businessName',
            'lat', 'lon', 'products', 'address',
        )

