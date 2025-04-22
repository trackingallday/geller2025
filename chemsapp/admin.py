# -*- coding: utf-8 -*-
from django.contrib import admin
import pytz
from chemsapp.models import SafetyWear, Distributor, Customer, Profile,\
    Product, ProductAdd, ProductRemove, ProductCategory, Post, MarketCategory, Config, Contact, Size,\
    Sector, NewsPost, SectorSection
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


@admin.register(SafetyWear)
class SafetyWearAdmin(ImportExportModelAdmin):
    resource_class = SafetyWearResource


@admin.register(Distributor)
class DistributorAdmin(ImportExportModelAdmin):
    resource_class = DistributorResource


@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):
    search_fields = ['address', 'businessName',]
    resource_class = CustomerResource


class ProfileAdmin(admin.ModelAdmin):
    pass


class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Product)
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


@admin.register(ProductCategory)
class CategoryAdmin(ImportExportModelAdmin):
    form = ProductCategoryForm
    pass

@admin.register(Post)
class PostAdmin(ImportExportModelAdmin):
    form = PostForm
    pass

@admin.register(MarketCategory)
class MarketAdmin(ImportExportModelAdmin):
    pass

@admin.register(Contact)
class ContactAdmin(ImportExportModelAdmin):
    def _created_at(self, obj):
        return obj.created_at.astimezone(pytz.timezone('Pacific/Auckland')).strftime('%c')
    list_display = ['nameFrom', 'emailFrom', '_created_at']
    search_fields = ['nameFrom', 'emailFrom', 'companyName',]


@admin.register(Config)
class ConfigAdmin(ImportExportModelAdmin):
    read_only_fields = ('name', )

@admin.register(Size)
class SizeAdmin(ImportExportModelAdmin):
    pass


class SectorSectionInline(admin.TabularInline):  # or admin.StackedInline
    model = SectorSection
    extra = 1  # Number of empty forms to display
    fields = ('title', 'description', 'image', 'image_preview')
    readonly_fields = ('image_preview',)
    
    @admin.display(
        description='Preview'
    )
    def image_preview(self, obj):
        if obj.image:
            return '<img src="%s" style="max-height: 100px; max-width: 100px;" />' % obj.image.url
        return "No image"

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    inlines = [SectorSectionInline]

@admin.register(NewsPost)
class NewsPostAdmin(ImportExportModelAdmin):
    pass


admin.site.register(Profile, ProfileAdmin)
