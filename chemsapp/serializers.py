from django.contrib.auth.models import User
from chemsapp.models import ProductRemove, Distributor, ProductAdd, Product, Customer, Profile, SafetyWear, ProductCategory,\
    Post, MarketCategory, Config, Contact, Size, MarketSector, NewsArticle, MarketSectorSection
from rest_framework import serializers
import pyqrcode
import base64
import io
import chemicaldatasheets.settings


def path_to_qr_code(path):
    if not path:
        return ""
    base_url = 'http://geller.co.nz'
    base_data_url = 'data:image/svg+xml;base64,'
    link = base_url + path.url
    url = pyqrcode.create(link)
    buffer = io.BytesIO()
    url.svg(buffer)
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
            'id', 'name', 'menu_color', 'description', 'image', 'isSubCategory', 'relatedCategory',
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
            'id', 'name', 'subheading', 'primaryImageLink', 'secondaryImageLink', 'usageType', 'amountDesc',
            'directions', 'productCode', 'productCodes', 'brand', 'infoSheet', 'sdsSheet', 'application', 'properties',
            'safetyWears', 'customers', 'editable',  'markets', 'description', 'subCategory', 'productCategory',
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
            'id', 'name', 'subheading', 'primaryImageLink', 'secondaryImageLink',
            'productCode', 'productCodes', 'brand', 'infoSheet', 'productCategory',
            'description', 'markets', 'directions', 'subCategory',
            'sizes',

        )


class ProductSheetSerializer(serializers.ModelSerializer):

    safetyWears = SafetyWearSerializer(many=True, read_only=True)
    sdsQrcode = serializers.SerializerMethodField('sds_qrcode')

    class Meta:
        model = Product
        read_only_fields = ('editable', 'customers')
        fields = (
            'name', 'subheading', 'primaryImageLink', 'secondaryImageLink', 'usageType', 'amountDesc',
            'directions', 'productCode', 'productCodes', 'brand', 'sdsSheet',
            'safetyWears', 'sdsQrcode',
        )

    def sds_qrcode(self, obj):
        return path_to_qr_code(obj.sdsSheet)


class DistributorSerializer(serializers.ModelSerializer):

    # Maintain backward compatibility: return first user as 'user'
    user = serializers.SerializerMethodField()
    # New field: return all users
    users = UserSerializer(many=True, read_only=True)
    customers = serializers.StringRelatedField(many=True, read_only=True)

    def get_user(self, obj):
        """Return the first user for backward compatibility"""
        first_user = obj.users.first()
        if first_user:
            return UserSerializer(first_user).data
        return None

    class Meta:
        model = Distributor
        fields = (
            'id', 'phonenumber', 'user', 'users', 'cellphonenumber', 'businessname',
            'customers', 'address', 'geocodingdetail', 'primaryimagelink',
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
        # Return the first distributor (for backward compatibility)
        first_distributor = obj.distributors.first()
        if first_distributor:
            return DistributorSerializer(first_distributor, many=False, read_only=True).data
        return None



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
        # Return comma-separated list of distributor business names
        distributor_names = [d.businessname for d in obj.distributors.all()]
        if not distributor_names:
            return "None"
        return ", ".join(distributor_names)


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
            'id', 'name', 'subheading', 'brand', 'customers',
        )


class PostSererializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = (
            'id', 'title', 'name', 'content', 'image',
            'page', 'linkURL', 'linkText', 'linkColor',
            'created_at', 'updated_at', 'author',
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
            'id', 'nameFrom', 'emailFrom', 'replied', 'content', 'isSDSDownload', 'companyName'
        )

class SizeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Size
        fields = (
            'id', 'name', 'desc', 'amount', 'image', 'imageNo', 'isBag',
        )

class NewsPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = (
            'id', 'title', 'name', 'content', 'image',
            'page', 'linkURL', 'linkText', 'linkColor',
            'created_at', 'updated_at', 'postType', 'postDate',
            'isFeatured', 'isActive', 'author',
        )

class SectorSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSectorSection
        fields = (
            'id', 'title', 'description', 'image'
        )
        
class SectorSerializer(serializers.ModelSerializer):
    product_feature = ProductSerializer(many=False, read_only=True)
    news_post_1 = NewsPostSerializer(many=False, read_only=True)
    news_post_2 = NewsPostSerializer(many=False, read_only=True)
    sections = SectorSectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = MarketSector
        fields = (
            'id', 'name', 'description', 'image', 
            'product_feature', 'product_feature_title', 
            'product_feature_desccription', 'product_feature_image',
            'news_post_1', 'news_post_2', 'created_at', 'updated_at',
            'sections'
        )
