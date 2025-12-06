# -*- coding: utf-8 -*-
from django.contrib import admin
import pytz
from chemsapp.models import SafetyWear, Distributor, Customer, Profile,\
    Product, ProductAdd, ProductRemove, ProductCategory, Post, MarketCategory, Config, Contact, Size,\
    MarketSector, MarketSectorSection, NewsArticle
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .forms import ProductCategoryForm, PostForm, SpecialPostForm
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.html import format_html


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
    list_display = ['name', 'page', 'title', 'created_at']
    list_filter = ['page']
    search_fields = ['name', 'title', 'page']

    class Media:
        css = {
            'all': ('admin/css/changelists.css',)
        }

    def changelist_view(self, request, extra_context=None):
        """Add link to special posts view"""
        extra_context = extra_context or {}
        extra_context['special_posts_url'] = reverse('admin:chemsapp_post_special')
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('special-posts/', self.admin_site.admin_view(self.special_posts_view), name='chemsapp_post_special'),
            path('special-posts/<int:post_id>/edit/', self.admin_site.admin_view(self.edit_special_post_view), name='chemsapp_post_special_edit'),
        ]
        return custom_urls + urls

    def special_posts_view(self, request):
        """View to display special posts grouped by page type"""
        # Define the special posts that must exist (case-insensitive filtering)
        home_posts = Post.objects.filter(page__iexact='Home').exclude(name__isnull=True).exclude(name='').order_by('name')
        about_posts = Post.objects.filter(page__iexact='About').exclude(name__isnull=True).exclude(name='').order_by('name')
        support_posts = Post.objects.filter(page__iexact='Support').exclude(name__isnull=True).exclude(name='').order_by('name')

        context = {
            'title': 'Manage Special Posts',
            'home_posts': home_posts,
            'about_posts': about_posts,
            'support_posts': support_posts,
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
            'has_permission': True,
        }
        return render(request, 'admin/chemsapp/post/special_posts.html', context)

    def edit_special_post_view(self, request, post_id):
        """View to edit a special post with readonly name field"""
        post = get_object_or_404(Post, pk=post_id)

        if request.method == 'POST':
            form = SpecialPostForm(request.POST, request.FILES, instance=post)
            if form.is_valid():
                form.save()
                messages.success(request, f'Post "{post.name}" updated successfully.')
                return redirect('admin:chemsapp_post_special')
        else:
            form = SpecialPostForm(instance=post)

        context = {
            'title': f'Edit Special Post: {post.name}',
            'form': form,
            'post': post,
            'opts': self.model._meta,
            'has_permission': True,
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
        }
        return render(request, 'admin/chemsapp/post/edit_special_post.html', context)

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


class SectorSectionInline(admin.TabularInline):  # or admin.StackedInline
    model = MarketSectorSection
    extra = 1  # Number of empty forms to display
    fields = ('title', 'description', 'image', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return '<img src="%s" style="max-height: 100px; max-width: 100px;" />' % obj.image.url
        return "No image"
    image_preview.allow_tags = True
    image_preview.short_description = 'Preview'

class SectorAdmin(admin.ModelAdmin):
    inlines = [SectorSectionInline]

class NewsPostAdmin(ImportExportModelAdmin):
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
admin.site.register(NewsArticle, NewsPostAdmin)
admin.site.register(MarketCategory, MarketAdmin)
admin.site.register(MarketSector, SectorAdmin)
