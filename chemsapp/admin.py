from django.contrib import admin
from chemsapp.models import SafetyWear, Distributor, Customer, Profile,\
    Product, ProductAdd, ProductRemove


class SafetyWearAdmin(admin.ModelAdmin):
    pass


class DistributorAdmin(admin.ModelAdmin):
    pass


class CustomerAdmin(admin.ModelAdmin):
    pass


class ProfileAdmin(admin.ModelAdmin):
    pass


class UserAdmin(admin.ModelAdmin):
    pass


class ProductAdmin(admin.ModelAdmin):
    pass


class ProductAddAdmin(admin.ModelAdmin):
    pass


class ProductRemoveAdmin(admin.ModelAdmin):
    pass


class ProfileAdmin(admin.ModelAdmin):
    pass


admin.site.register(SafetyWear, SafetyWearAdmin)
admin.site.register(Distributor, DistributorAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductAdd, ProductAddAdmin)
admin.site.register(ProductRemove, ProductRemoveAdmin)
admin.site.register(Profile, ProfileAdmin)

