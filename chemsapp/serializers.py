from django.contrib.auth.models import User
from chemsapp.models import ProductRemove, ProductAdd, Product, Customer, Profile, SafetyWear
from rest_framework import serializers


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = (
            'phoneNumber',
            'cellPhoneNumber',
            'businessName',
            'address',
            'profileType',
            'hasSetPassword',
        )


class UserSerializer(serializers.ModelSerializer):

    profile = ProfileSerializer(many=False, read_only=True)

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'profile',
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


class ProductSerializer(serializers.ModelSerializer):

    editable = serializers.SerializerMethodField('get_can_edit')
    customers = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Product
        read_only_fields = ('editable', 'customers')
        fields = (
            'id', 'name', 'primaryImageLink', 'secondaryImageLink', 'usageType', 'amountDesc',
            'instructions', 'productCode', 'brand', 'infoSheet', 'sdsSheet',
            'safetyWears', 'customers', 'editable',
        )

    def get_can_edit(self, obj):
        if "user" in self.context:
            return obj.uploadedBy.id == self.context["user"].id
        return False

    def get_my_customers(self, obj):
        if "user" in self.context:
            user = self.context["user"]
            customers = user.profile.distributor.customers.filter(products=obj)
            print(customers)
            serializer = CustomerSerializer(customers, many=True)
            print(serializer.data)
            return serializer.data
        return []


class SafetyWearSerializer(serializers.ModelSerializer):

    class Meta:
        model = SafetyWear
        fields = (
            'id', 'name', 'imageLink',
        )

