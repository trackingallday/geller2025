from django.db import models
from django.contrib.auth.models import User


class MyBaseModel(models.model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)


class Profile(models.Model, MyBaseModel):
    user = models.OneToOneField(User)
    phone_number = models.CharField(max_length=100)
    cell_phone_number = models.CharField(max_length=100)
    business_name = models.CharField(max_length=255)
    lat = models.DecimalField()
    lon = models.DecimalField()

    def __str__(self):
        return '%s %s %s'.format(self.business_name, self.user.first_name, self.user.last_name)


class Product(models.Model, MyBaseModel):
    name = models.CharField(max_length=255, unique=True)
    primaryImageLink = models.CharField(max_length=500)
    secondaryImageLink = models.CharField(max_length=500)
    usageType = models.CharField(max_length=455)
    amountDesc = models.CharField(max_length=455)
    instructions = models.TextField(max_length=2000)
    productCode = models.CharField(max_length=255, unique=True)
    brand = models.CharField(max_length=255)
    infoSheetLink = models.CharField(max_length=255)
    sdsSheetLink = models.CharField(max_length=255)
    safetyWears = models.ManyToManyField("SafetyWear", related_name="products")

    def __str__(self):
        return '%s %s'.format(self.name, self.brand)


class Customer(Profile):
    products = models.ManyToManyField(Product, related_name="customers")


class Distributor(Profile):
    customers = models.ManyToManyField(Customer, related_name="distributors")


class ProductAdd(models.Model, MyBaseModel):
    product = models.ForeignKey(Product, related_name="productsAdds", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name="productAdds", on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, related_name="productAdds", on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s %s'.format(self.distributor.business_name, self.customer.business_name, self.product.name)


class ProductRemove(models.Model, MyBaseModel):
    product = models.ForeignKey(Product, related_name="productsRemoves", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name="productRemoves", on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, related_name="productRemoves", on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s %s'.format(self.distributor.business_name, self.customer.business_name, self.product.name)


class SafetyWear(models.Model, MyBaseModel):
    name = models.CharField(max_length=255)
    imageLink = models.CharField(max_length=455)
    def __str__(self):
        return self.name

