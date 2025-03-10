from django.contrib import admin
import pytz
from chemsapp.models import SafetyWear, Distributor, Customer, Profile,\
    Product, ProductAdd, ProductRemove, ProductCategory, Post, MarketCategory, Config, Contact, Size
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .forms import ProductCategoryForm, PostForm


class SafetyWearResource(resources.ModelResource):
    class Meta:
        model = SafetyWear


class DistributorResource(resources.ModelResource):
    class Meta:
        model = Distributor


class CustomerResource(resources.ModelResource):
    class Meta:
        model = Customer


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product


class SafetyWearAdmin(ImportExportModelAdmin):
    resource_class = SafetyWearResource


class DistributorAdmin(ImportExportModelAdmin):
    resource_class = DistributorResource


class CustomerAdmin(ImportExportModelAdmin):
    search_fields = ['address', 'businessName',]
    resource_class = CustomerResource


class ProfileAdmin(admin.ModelAdmin):
    pass


class UserAdmin(admin.ModelAdmin):
    pass


class ProductAdmin(ImportExportModelAdmin):
    search_fields = ['name',]
    readonly_fields = ["properties", "application"]
    resource_class = ProductResource


#class ProductAddAdmin(ImportExportModelAdmin):
#    pass


#class ProductRemoveAdmin(ImportExportModelAdmin):
#    pass


class ProfileAdmin(ImportExportModelAdmin):
    pass


class CategoryAdmin(ImportExportModelAdmin):
    form = ProductCategoryForm
    pass

class PostAdmin(ImportExportModelAdmin):
    form = PostForm
    pass

class MarketAdmin(ImportExportModelAdmin):
    pass

class ContactAdmin(ImportExportModelAdmin):
    def _created_at(self, obj):
        return obj.created_at.astimezone(pytz.timezone('Pacific/Auckland')).strftime('%c')
    list_display = ['nameFrom', 'emailFrom', '_created_at']
    search_fields = ['nameFrom', 'emailFrom', 'companyName',]


class ConfigAdmin(ImportExportModelAdmin):
    read_only_fields = ('name', )

class SizeAdmin(ImportExportModelAdmin):
    pass


admin.site.register(SafetyWear, SafetyWearAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Size, SizeAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(Distributor, DistributorAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(ProductCategory, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(MarketCategory, MarketAdmin)
