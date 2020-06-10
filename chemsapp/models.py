from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from rest_framework.authtoken.models import Token
from django.core.files.storage import FileSystemStorage
import cloudinary
import cloudinary.uploader
import cloudinary.api

typeChoices = [("customer", "customer"), ("distributor", "distributor"), ("admin", "admin")]


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class MyBaseModel:
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)


class Profile(MyBaseModel, models.Model):
    user = models.OneToOneField(User, unique=True)
    phoneNumber = models.CharField(max_length=100)
    cellPhoneNumber = models.CharField(max_length=100)
    businessName = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    profileType = models.CharField(choices=typeChoices, default="customer",
                                   max_length=255, blank=True, null=True)
    hasSetPassword = models.BooleanField(default=False)

    def __str__(self):
        return "{} {} {} {} {}".format(self.businessName, self.user.first_name, self.user.last_name, self.user.email, self.user.username)


class ProductCategory(MyBaseModel, models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=1000)
    products = models.ManyToManyField('Product', blank=True, null=True, related_name='categories')
    image = models.FileField(upload_to='documents/', blank=True, null=True)
    menu_color = models.CharField(max_length=7, blank=True, null=True, help_text=mark_safe('Choose a color for the category menu. See <a href="https://www.w3schools.com/colors/colors_picker.asp">W3Schools Color Picker</a> for help choosing a color. If black (#000000) is chosen, a default color will be used.'))
    isSubCategory = models.BooleanField(default=False)
    relatedCategory = models.ManyToManyField('ProductCategory', blank=True)

    def __str__(self):
        return "{} ".format(self.name)


class Product(MyBaseModel, models.Model):
    name = models.CharField(max_length=255, unique=True)
    subheading = models.CharField(max_length=255, blank=True, null=True)
    secondaryImageLink = models.FileField(upload_to='documents/', blank=True, null=True)
    primaryImageLink  = models.FileField(upload_to='documents/', blank=True, null=True)
    usageType = models.CharField(max_length=455)
    amountDesc = models.CharField(max_length=455)
    instructions = models.TextField(max_length=2000)
    productCode = models.CharField(max_length=255, unique=True)
    productCodes = models.TextField(max_length=1000, blank=True, null=True)
    brand = models.CharField(max_length=255)
    infoSheet = models.FileField(upload_to='documents/', blank=True, null=True)
    sdsSheet = models.FileField(upload_to='documents/', blank=True, null=True)
    safetyWears = models.ManyToManyField("SafetyWear", related_name="products", blank=True)
    uploadedBy = models.ForeignKey(User, on_delete=None, related_name="products_added")
    description = models.TextField(max_length=1000, blank=True, null=True)
    subCategory = models.ManyToManyField(ProductCategory, blank=True, null=True, related_name='subcategories')
    properties = models.CharField(max_length=500, blank=True, null=True)
    public = models.BooleanField(default=False)
    productCategory = models.ManyToManyField(ProductCategory, through=ProductCategory.products.through, blank=True, null=True, related_name='categories')
    application = models.CharField(max_length=500, blank=True, null=True)
    sizes = models.ManyToManyField("Size", related_name="products", blank=True)

    def __str__(self):
        return "{} ".format(self.name)


class Post(MyBaseModel, models.Model):
    name = models.CharField(max_length=500, blank=True, null=True)
    page = models.CharField(max_length=100)
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(max_length=2000, blank=True, null=True)
    image = models.FileField(upload_to='documents/', blank=True, null=True)
    linkURL = models.CharField(max_length=1000, blank=True, null=True)
    linkText = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return "{} {} {}".format(self.page, self.title, self.name)


class MarketCategory(MyBaseModel, models.Model):
    name = models.CharField(max_length=500, blank=True, null=True)
    image = models.FileField(upload_to='documents/', blank=True, null=True)
    products = models.ManyToManyField(Product, related_name="markets", blank=True, null=True)

    def __str__(self):
        return "{}".format(self.name)


class Customer(Profile):
    products = models.ManyToManyField(Product, related_name="customers", blank=True, null=True)
    geocodingDetail = models.TextField(max_length=1500, blank=True, null=True)
    distributorParent = models.ForeignKey('Distributor', blank=True, null=True)

    def __str__(self):
        return "{} {} {}".format(self.businessName, self.user.email, self.distributorParent)


class Distributor(Profile):
    customers = models.ManyToManyField(Customer, related_name="distributors", blank=True, null=True)
    geocodingDetail = models.TextField(max_length=1500, blank=True, null=True)
    primaryImageLink  = models.FileField(upload_to='documents/', blank=True, null=True)


class ProductAdd(MyBaseModel, models.Model):
    productAdded = models.ForeignKey(Product, related_name="productsAdds", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name="productAdds", on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, related_name="productAdds", on_delete=models.CASCADE)

    def __str__(self):
        return "{} {} {}".format(self.distributor.businessName, self.customer.businessName, self.productAdded.name)


class ProductRemove(MyBaseModel, models.Model):
    productRemoved = models.ForeignKey(Product, related_name="productsRemoves", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name="productRemoves", on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, related_name="productRemoves", on_delete=models.CASCADE)

    def __str__(self):
        return "{} {} {}".format(self.distributor.business_name, self.customer.business_name, self.productRemoved.name)


class SafetyWear(MyBaseModel, models.Model):
    name = models.CharField(max_length=255)
    imageLink = models.CharField(max_length=455)

    def __str__(self):
        return self.name

class Config(MyBaseModel, models.Model):
    name = models.CharField(max_length=255)
    val = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Size(MyBaseModel, models.Model):
    name = models.CharField(max_length=255)
    desc = models.CharField(max_length=255)
    amount = models.CharField(max_length=255)
    image = models.FileField(upload_to='documents/', blank=True, null=True)
    imageNo = models.FileField(upload_to='documents/', blank=True, null=True)
    isBag = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Contact(MyBaseModel, models.Model):
    nameFrom = models.CharField(max_length=255)
    emailFrom = models.CharField(max_length=255)
    replied = models.BooleanField(default=False)
    content = models.TextField(max_length=1500)
    # New SDS Enquiry stuff
    isSDSDownload = models.BooleanField(default=False)
    companyName = models.TextField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return self.nameFrom
