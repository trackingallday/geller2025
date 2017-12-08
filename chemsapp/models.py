from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
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


class MyBaseModel():
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)


class Profile(MyBaseModel, models.Model):
    user = models.OneToOneField(User, unique=True)
    phoneNumber = models.CharField(max_length=100)
    cellPhoneNumber = models.CharField(max_length=100)
    businessName = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    lat = models.DecimalField(max_digits=80, decimal_places=8)
    lon = models.DecimalField(max_digits=80, decimal_places=8)
    profileType = models.CharField(choices=typeChoices, default="customer",
                                   max_length=255, null=True)
    hasSetPassword = models.BooleanField(default=False)

    def __str__(self):
        return "{} - {} - {}".format(self.businessName, self.user.first_name, self.user.last_name)


class Product(MyBaseModel, models.Model):
    name = models.CharField(max_length=255, unique=True)
    primaryImageLink = models.CharField(max_length=500)
    secondaryImageLink = models.CharField(max_length=500)
    usageType = models.CharField(max_length=455)
    amountDesc = models.CharField(max_length=455)
    instructions = models.TextField(max_length=2000)
    productCode = models.CharField(max_length=255, unique=True)
    brand = models.CharField(max_length=255)
    infoSheet = models.FileField(upload_to='documents/', null=True)
    sdsSheet = models.FileField(upload_to='documents/', null=True)
    safetyWears = models.ManyToManyField("SafetyWear", related_name="products")


    def __str__(self):
        return "{} ".format(self.name)


class Customer(Profile):
    products = models.ManyToManyField(Product, related_name="customers", null=True)


class Distributor(Profile):
    customers = models.ManyToManyField(Customer, related_name="distributors", null=True)


class ProductAdd(MyBaseModel, models.Model):
    productAdded = models.ForeignKey(Product, related_name="productsAdds", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name="productAdds", on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, related_name="productAdds", on_delete=models.CASCADE)

    def __str__(self):
        return "{} - {} - {}".format(self.distributor.businessName, self.customer.businessName, self.productAdded.name)


class ProductRemove(MyBaseModel, models.Model):
    productRemoved = models.ForeignKey(Product, related_name="productsRemoves", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name="productRemoves", on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, related_name="productRemoves", on_delete=models.CASCADE)

    def __str__(self):
        return "{} - {} - {}".format(self.distributor.business_name, self.customer.business_name, self.productRemoved.name)


class SafetyWear(MyBaseModel, models.Model):
    name = models.CharField(max_length=255)
    imageLink = models.CharField(max_length=455)

    def __str__(self):
        return self.name

