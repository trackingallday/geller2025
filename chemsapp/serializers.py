from django.contrib.auth.models import User
from chemsapp.models import ProductRemove, Distributor, ProductAdd, Product, Customer, Profile, SafetyWear, ProductCategory,\
    Post, MarketCategory, Config, Contact, Size
from rest_framework import serializers
import pyqrcode
import base64
import io
import chemicaldatasheets.settings


def path_to_qr_code(path):
    base_url = 'http://104.236.249.246'
    base_data_url = 'data:image/png;base64,'
    link = base_url + path.url
    url = pyqrcode.create(link.upper())
    buffer = io.BytesIO()
    url.png(buffer)
    encoded_string = base64.b64encode(buffer.getvalue()).decode()
    return base_data_url + encoded_string


class SafetyWearSerializer(serializers.ModelSerializer):

    class Meta:
        model = SafetyWear
        fields = (
            'id', 'name', 'imageLink',
        )


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductCategory
        fields = (
            'id', 'name', 'description', 'image', 'isSubCategory',
        )


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


class ProductSerializer(serializers.ModelSerializer):

    editable = serializers.SerializerMethodField('get_can_edit')
    customers = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Product
        read_only_fields = ('editable', 'customers')
        fields = (
            'id', 'name', 'primaryImageLink', 'secondaryImageLink', 'usageType', 'amountDesc',
            'instructions', 'productCode', 'brand', 'infoSheet', 'sdsSheet',
            'safetyWears', 'customers', 'editable',  'markets', 'properties', 'application', 'description', 'subCategory', 'productCategory',
            'sizes',
        )

    def get_can_edit(self, obj):
        if "user" in self.context:
            return obj.uploadedBy.id == self.context["user"].id
        return False


class PublicProductSerializer(serializers.ModelSerializer):

    markets = serializers.PrimaryKeyRelatedField(many=True, queryset=MarketCategory.objects.all())

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'primaryImageLink', 'secondaryImageLink',
            'productCode', 'brand', 'infoSheet', 'productCategory',
            'description', 'markets', 'properties', 'application', 'subCategory',
            'sizes',

        )


class ProductSheetSerializer(serializers.ModelSerializer):

    safetyWears = SafetyWearSerializer(many=True, read_only=True)
    sdsQrcode = serializers.SerializerMethodField('sds_qrcode')

    class Meta:
        model = Product
        read_only_fields = ('editable', 'customers')
        fields = (
            'name', 'primaryImageLink', 'secondaryImageLink', 'usageType', 'amountDesc',
            'instructions', 'productCode', 'brand', 'sdsSheet',
            'safetyWears', 'sdsQrcode',
        )

    def sds_qrcode(self, obj):
        return path_to_qr_code(obj.sdsSheet)


class DistributorSerializer(serializers.ModelSerializer):

    user = UserSerializer(many=False, read_only=True)
    customers = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Distributor
        fields = (
            'id', 'phoneNumber', 'user', 'cellPhoneNumber', 'businessName',
            'customers', 'address', 'geocodingDetail', 'primaryImageLink',
        )


class CustomerSheetSerializer(serializers.ModelSerializer):

    products = ProductSheetSerializer(many=True, read_only=True)
    distributor = serializers.SerializerMethodField('distributor_parent')

    class Meta:
        model = Customer
        fields = (
            'id', 'phoneNumber', 'user', 'cellPhoneNumber', 'businessName',
            'products', 'address', 'geocodingDetail', 'distributor',
        )

    def distributor_parent(self, obj):
        return DistributorSerializer(obj.distributorParent, many=False, read_only=True).data



class CustomerSerializer(serializers.ModelSerializer):

    user = UserSerializer(many=False, read_only=True)
    products = serializers.StringRelatedField(many=True, read_only=True)
    productsExpanded = serializers.SerializerMethodField('products_expanded')
    distributor = serializers.SerializerMethodField('distributor_parent')

    class Meta:
        model = Customer
        fields = (
            'id', 'phoneNumber', 'user', 'cellPhoneNumber', 'businessName',
            'products', 'address', 'geocodingDetail', 'productsExpanded', 'distributor',
        )

    def products_expanded(self, obj):
        return ProductSerializer(obj.products, many=True).data

    def distributor_parent(self, obj):
        if not obj.distributorParent:
            print('NOOOOO', obj.user.email)
            return "None"
        return obj.distributorParent.businessName


class CustomerMapSerializer(serializers.ModelSerializer):

    distributors = DistributorSerializer(many=True, read_only=True)
    products = serializers.StringRelatedField(many=True, read_only=True)
    productIds = serializers.SerializerMethodField('product_ids')

    class Meta:
        model = Customer
        read_only_fields = ('distributors', 'products')
        fields = (
            'geocodingDetail',
            'id',
            'businessName',
            'products',
            'distributors',
            'products',
            'productIds',
        )


    def product_ids(self, obj):
        return [p.id for p in obj.products.all()]


class ProductMapSerializer(serializers.ModelSerializer):

    customers = CustomerMapSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        read_only_fields = ('customers', )
        fields = (
            'id', 'name', 'brand', 'customers',
        )


class PostSererializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = (
            'id', 'title', 'name', 'content', 'image', 'page',
        )


class MarketSerializer(serializers.ModelSerializer):

    class Meta:
        model = MarketCategory
        fields = (
            'id', 'name', 'image',
        )

class ConfigSerializer(serializers.ModelSerializer):

    class Meta:
        model = Config
        fields = (
            'id', 'name', 'val',

        )

class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = (
            'id', 'nameFrom', 'emailFrom', 'replied', 'content',

        )

class SizeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Size
        fields = (
            'id', 'name', 'desc', 'amount', 'image', 'imageNo',
        )
