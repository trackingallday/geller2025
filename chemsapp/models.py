# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from rest_framework.authtoken.models import Token
from django.core.files.storage import FileSystemStorage
from ckeditor.fields import RichTextField


typeChoices = [("customer", "customer"), ("distributor", "distributor"), ("admin", "admin")]


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance=None, created=False, **kwargs):
    if created and not hasattr(instance, 'profile'):
        # Create a basic profile for new users
        Profile.objects.create(
            user=instance,
            phoneNumber='',
            businessName=instance.get_full_name() or instance.username,
            address='',
        )


class MyBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class Profile(MyBaseModel):
    user = models.OneToOneField(User, unique=True, on_delete=models.CASCADE, related_name="profile")
    phoneNumber = models.CharField(max_length=100)
    cellPhoneNumber = models.CharField(max_length=100, blank=True, null=True)
    businessName = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    profileType = models.CharField(choices=typeChoices, default="customer",
                                    max_length=255, blank=True, null=True)
    hasSetPassword = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Delete any existing profiles for this user before saving a new Customer
        if not self.pk and self.user_id and self.__class__.__name__ in ['Customer']:
            Profile.objects.filter(user_id=self.user_id).delete()
        super().save(*args, **kwargs)

    def validate_unique(self, exclude=None):
        # Skip validation for user uniqueness when creating Customer
        # because we'll delete the old profile in save()
        if not self.pk and self.__class__.__name__ in ['Customer']:
            return
        super().validate_unique(exclude=exclude)

    @property
    def distributor(self):
        """
        Returns the distributor this user belongs to (if any).
        Maintains backward compatibility with request.user.profile.distributor pattern.
        """
        if self.profileType == 'distributor':
            return self.user.distributors.first()
        return None

    def __str__(self):
        return "{} {} {} {} {}".format(self.businessName, self.user.first_name, self.user.last_name, self.user.email, self.user.username)


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=1000)
    products = models.ManyToManyField('Product', blank=True, related_name='categories')
    image = models.FileField(upload_to='documents/', blank=True, null=True)
    menu_color = models.CharField(max_length=7, blank=True, null=True, help_text=mark_safe('Choose a color for the category menu. See <a href="https://www.w3schools.com/colors/colors_picker.asp">W3Schools Color Picker</a> for help choosing a color. If black (#000000) is chosen, a default color will be used.'))
    isSubCategory = models.BooleanField(default=False)
    relatedCategory = models.ManyToManyField('ProductCategory', blank=True)

    def __str__(self):
        return "{} ".format(self.name)


class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    subheading = models.CharField(max_length=255, blank=True, null=True)
    secondaryImageLink = models.FileField(upload_to='documents/', blank=True, null=True)
    primaryImageLink  = models.FileField(upload_to='documents/', blank=True, null=True)
    description = RichTextField()
    directions = RichTextField()
    productCode = models.CharField(max_length=255, unique=True)
    productCodes = models.TextField(max_length=1000, blank=True, null=True)
    brand = models.CharField(max_length=255)
    infoSheet = models.FileField(upload_to='documents/', blank=True, null=True)
    sdsSheet = models.FileField(upload_to='documents/', blank=True, null=True)
    safetyWears = models.ManyToManyField("SafetyWear", related_name="products", blank=True)
    uploadedBy = models.ForeignKey(User, related_name="products_added", on_delete=models.CASCADE, blank=True, null=True)
    subCategory = models.ManyToManyField(ProductCategory, blank=True, related_name='subcategories')
    public = models.BooleanField(default=False)
    productCategory = models.ManyToManyField(ProductCategory, through=ProductCategory.products.through, blank=True, related_name='categories')
    sizes = models.ManyToManyField("Size", related_name="products", blank=True)

    # Unused for marketing frontend
    usageType = models.CharField(max_length=455, blank=True)
    amountDesc = models.CharField(max_length=455, blank=True)

    # Old fields that are now read-only in the admin.
    properties = models.CharField(max_length=500, blank=True, null=True, help_text='Read only: Legacy field is no longer used. Exists only for reference.')
    application = models.CharField(max_length=500, blank=True, null=True, help_text='Read only: Legacy field is no longer used. Exists only for reference.')

    def __str__(self):
        return f'{self.name}'


class ProductVariant(models.Model):
    code = models.CharField(max_length=255, unique=True, null=True, blank=True)
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    size = models.ForeignKey('Size', related_name='variants', on_delete=models.SET_NULL, blank=True, null=True)
    pack_size = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    barcode = models.CharField(max_length=255)
    image = models.FileField(upload_to='documents/', blank=True, null=True)

    def __str__(self):
        size_str = f' ({self.size})' if self.size else ''
        return f'{self.product.name}{size_str} - {self.barcode}'


class CustomerContact(models.Model):
    customer = models.ForeignKey('Customer', related_name='contacts', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, default='')
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    receive_report = models.BooleanField(default=False, help_text='Email the report to this contact')

    def __str__(self):
        return f'{self.name} ({self.customer})'


class CustomerProductVariant(models.Model):
    customer = models.ForeignKey('Customer', related_name='product_variants', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, related_name='customer_variants', on_delete=models.CASCADE)
    max_stock_level = models.IntegerField()

    def __str__(self):
        return f'{self.customer} - {self.product_variant}'


class Post(MyBaseModel):
    name = models.CharField(max_length=500, blank=True, null=True)
    page = models.CharField(max_length=100)
    title = models.CharField(max_length=255, blank=True, null=True)
    content = RichTextField()
    image = models.FileField(upload_to='documents/', blank=True, null=True)
    linkURL = models.CharField(max_length=1000, blank=True, null=True)
    linkText = models.CharField(max_length=255, blank=True, null=True)
    linkColor = models.CharField(max_length=7, blank=True, null=True, help_text=mark_safe('Choose a color for the category menu. See <a href="https://www.w3schools.com/colors/colors_picker.asp">W3Schools Color Picker</a> for help choosing a color. If black (#000000) is chosen, a default color will be used.'))
    author = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return "{} {} {}".format(self.page, self.title, self.name)
    
class NewsArticle(Post):
    
    postType = models.CharField(max_length=100, blank=True, null=True)
    postDate = models.DateTimeField(auto_now_add=True)
    isFeatured = models.BooleanField(default=False)
    isActive = models.BooleanField(default=False)

    def __str__(self):
        return "{} {} {}".format(self.page, self.title, self.name)

class MarketSector(MyBaseModel):
    name = models.CharField(max_length=500, blank=True, null=True)
    description = RichTextField()
    image = models.FileField(upload_to='documents/', blank=True, null=True)
    product_feature = models.ForeignKey(Product, related_name="sectors", blank=True, null=True, on_delete=models.CASCADE)
    product_feature_title = models.CharField(max_length=100, blank=True, null=True)
    product_feature_desccription = models.CharField(max_length=1000, blank=True, null=True)
    product_feature_image = models.FileField(upload_to='documents/', blank=True, null=True)
    #news_post_1 = models.ForeignKey(NewsArticle, related_name="sectors", blank=True, null=True, on_delete=models.CASCADE)
    #news_post_2 = models.ForeignKey(NewsArticle, related_name="sectors_2", blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class MarketSectorSection(MyBaseModel):
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    image = models.FileField(upload_to='documents/', blank=True, null=True)
    sector = models.ForeignKey(MarketSector, related_name="sections", blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return "{}".format(self.title)

class SectorSolution(MyBaseModel):
    name = models.CharField(max_length=500, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(max_length=1000, blank=True, null=True)
    content_title = models.CharField(max_length=255, blank=True, null=True)
    content_image = models.FileField(upload_to='documents/', blank=True, null=True)
    content2_title = models.CharField(max_length=255, blank=True, null=True)
    content2 = models.TextField(max_length=1000, blank=True, null=True)
    content2_image = models.FileField(upload_to='documents/', blank=True, null=True)
    content3_title = models.CharField(max_length=255, blank=True, null=True)
    content3 = models.TextField(max_length=1000, blank=True, null=True)
    footer_title = models.CharField(max_length=255, blank=True, null=True)
    footer_subtitle = models.CharField(max_length=255, blank=True, null=True)
    footer_image = models.FileField(upload_to='documents/', blank=True, null=True)
    footer_subtitle2 = models.CharField(max_length=255, blank=True, null=True)
    extra = models.TextField(max_length=1000, blank=True, null=True)


    def __str__(self):
        return "{}".format(self.name)


class MarketCategory(models.Model):
    name = models.CharField(max_length=500, blank=True, null=True)
    image = models.FileField(upload_to='documents/', blank=True, null=True)
    products = models.ManyToManyField(Product, related_name="markets", blank=True)

    def __str__(self):
        return "{}".format(self.name)


class Customer(Profile):
    products = models.ManyToManyField(Product, related_name="customers", blank=True)
    geocodingDetail = models.TextField(max_length=1500, blank=True, null=True)

    def __str__(self):
        distributor_names = ", ".join([d.businessname for d in self.distributors.all()[:3]])
        return "{} {} {}".format(self.businessName, self.user.email, distributor_names if distributor_names else "No distributor")


class Distributor(MyBaseModel):
    # Multiple users can be associated with one distributor
    users = models.ManyToManyField(User, related_name='distributors', blank=True)

    # Fields from Profile model
    phonenumber = models.CharField(max_length=100, default='')
    cellphonenumber = models.CharField(max_length=100, blank=True, null=True)
    businessname = models.CharField(max_length=255, default='')
    address = models.CharField(max_length=500, default='')
    profiletype = models.CharField(choices=typeChoices, default="distributor",
                                    max_length=255, blank=True, null=True)
    hassetpassword = models.BooleanField(default=False)

    # Distributor-specific fields
    customers = models.ManyToManyField(Customer, related_name="distributors", blank=True)
    geocodingdetail = models.TextField(max_length=1500, blank=True, null=True)
    primaryimagelink = models.FileField(upload_to='documents/', blank=True, null=True)

    def __str__(self):
        return "{} {}".format(self.businessname, self.address)

    # Backward compatibility properties for camelCase access
    @property
    def businessName(self):
        """Backward compatibility for businessName (correct spelling)"""
        return self.businessname

    @property
    def phoneNumber(self):
        """Backward compatibility for phoneNumber"""
        return self.phonenumber

    @property
    def cellPhoneNumber(self):
        """Backward compatibility for cellPhoneNumber"""
        return self.cellphonenumber

    @property
    def profileType(self):
        """Backward compatibility for profileType"""
        return self.profiletype

    @property
    def hasSetPassword(self):
        """Backward compatibility for hasSetPassword"""
        return self.hassetpassword

    @property
    def geocodingDetail(self):
        """Backward compatibility for geocodingDetail"""
        return self.geocodingdetail

    @property
    def primaryImageLink(self):
        """Backward compatibility for primaryImageLink"""
        return self.primaryimagelink


class ProductAdd(models.Model):
    productAdded = models.ForeignKey(Product, related_name="productsAdds", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name="productAdds", on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, related_name="productAdds", on_delete=models.CASCADE)

    def __str__(self):
        return "{} {} {}".format(self.distributor.businessname, self.customer.businessName, self.productAdded.name)


class ProductRemove(models.Model):
    productRemoved = models.ForeignKey(Product, related_name="productsRemoves", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name="productRemoves", on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, related_name="productRemoves", on_delete=models.CASCADE)

    def __str__(self):
        return "{} {} {}".format(self.distributor.businessname, self.customer.businessName, self.productRemoved.name)


class SafetyWear(models.Model):
    name = models.CharField(max_length=255)
    imageLink = models.CharField(max_length=455)

    def __str__(self):
        return self.name

class Config(models.Model):
    name = models.CharField(max_length=255)
    val = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=255)
    desc = models.CharField(max_length=255)
    amount = models.CharField(max_length=255)
    image = models.FileField(upload_to='documents/', blank=True, null=True)
    imageNo = models.FileField(upload_to='documents/', blank=True, null=True)
    isBag = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Contact(MyBaseModel):
    nameFrom = models.CharField(max_length=255)
    emailFrom = models.CharField(max_length=255)
    replied = models.BooleanField(default=False)
    content = models.TextField(max_length=1500)
    # New SDS Enquiry stuff
    isSDSDownload = models.BooleanField(default=False)
    companyName = models.TextField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return self.nameFrom


# Map each model to the FileField names that hold images (not PDFs/docs).
_IMAGE_FIELDS = {
    ProductCategory: ['image'],
    Product: ['primaryImageLink', 'secondaryImageLink'],
    ProductVariant: ['image'],
    Post: ['image'],
    NewsArticle: ['image'],
    MarketSector: ['image', 'product_feature_image'],
    MarketSectorSection: ['image'],
    SectorSolution: ['content_image', 'content2_image', 'footer_image'],
    MarketCategory: ['image'],
    Distributor: ['primaryimagelink'],
    Size: ['image', 'imageNo'],
}


def _downscale_model_images(sender, instance, **kwargs):
    from chemsapp.views import downscale_image
    fields = _IMAGE_FIELDS.get(sender, [])
    for field_name in fields:
        file_field = getattr(instance, field_name, None)
        if file_field and file_field.name:
            try:
                downscale_image(file_field.path)
            except Exception:
                pass


for _model in _IMAGE_FIELDS:
    post_save.connect(_downscale_model_images, sender=_model)
