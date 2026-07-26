# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.utils.html import format_html
import pytz
from chemsapp.models import SafetyWear, Distributor, Customer, Profile,\
    Product, ProductAdd, ProductRemove, ProductCategory, Post, MarketCategory, Config, Contact, Size,\
    MarketSector, MarketSectorSection, NewsArticle, ProductVariant, CustomerProductVariant, CustomerContact,\
    FillType, VariantFillOverride
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .forms import ProductCategoryForm, PostForm, SpecialPostForm, DistributorAdminForm, DistributorUserInlineForm, ProductForm
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages


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
    list_display = ['name', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.imageLink:
            return format_html('<img src="{}" style="max-height:40px; max-width:40px;" />', obj.imageLink.url)
        return '-'
    image_preview.short_description = 'Preview'


class DistributorAdmin(ImportExportModelAdmin):
    resource_class = DistributorResource
    form = DistributorAdminForm

    # List display
    list_display = ['businessname', 'address', 'phonenumber', 'users_count', 'customers_count', 'created_at']
    list_filter = ['created_at', 'updated_at', 'profiletype']
    search_fields = ['businessname', 'address', 'phonenumber', 'cellphonenumber']

    # Field organization
    fieldsets = (
        ('Business Information', {
            'fields': ('businessname', 'address', 'phonenumber', 'cellphonenumber')
        }),
        ('Additional Details', {
            'fields': ('geocodingdetail', 'primaryimagelink', 'profiletype', 'hassetpassword', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Relationships', {
            'fields': ('users', 'customers'),
            'description': 'Associate existing users and customers with this distributor. To create new users, use the "Quick Actions" box above or the "Create new user for distributor" action.'
        }),
    )

    # Use filter_horizontal for better ManyToMany field UX
    filter_horizontal = ['users', 'customers']

    # Actions
    actions = ['send_password_reset_emails', 'display_user_info', 'create_user_for_distributor']

    # Read-only fields
    readonly_fields = ['created_at', 'updated_at']

    def get_urls(self):
        """Add custom URLs for user creation"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:distributor_id>/create-user/',
                self.admin_site.admin_view(self.create_user_view),
                name='chemsapp_distributor_create_user'
            ),
        ]
        return custom_urls + urls

    def users_count(self, obj):
        """Display count of associated users"""
        count = obj.users.count()
        if count > 0:
            user_names = ', '.join([f"{u.username}" for u in obj.users.all()[:3]])
            if count > 3:
                user_names += f" (+{count - 3} more)"
            return format_html('<span title="{}">{}</span>', user_names, count)
        return '0'
    users_count.short_description = 'Users'

    def customers_count(self, obj):
        """Display count of associated customers"""
        return obj.customers.count()
    customers_count.short_description = 'Customers'

    def send_password_reset_emails(self, request, queryset):
        """Send password reset emails to all users associated with selected distributors"""
        total_sent = 0
        for distributor in queryset:
            for user in distributor.users.all():
                if user.email:
                    form = PasswordResetForm({'email': user.email})
                    if form.is_valid():
                        form.save(
                            request=request,
                            use_https=request.is_secure(),
                            email_template_name='registration/password_reset_email.html',
                        )
                        total_sent += 1

        self.message_user(
            request,
            f'Password reset emails sent to {total_sent} user(s).',
            messages.SUCCESS
        )
    send_password_reset_emails.short_description = "Send password reset emails to distributor users"

    def display_user_info(self, request, queryset):
        """Display detailed user information for selected distributors"""
        info = []
        for distributor in queryset:
            users = distributor.users.all()
            if users:
                info.append(f"<strong>{distributor.businessname}</strong>:")
                for user in users:
                    profile_phone = ''
                    try:
                        profile_phone = f" (Phone: {user.profile.phoneNumber})" if user.profile.phoneNumber else ''
                    except:
                        pass
                    info.append(f"  - {user.username} ({user.email}){profile_phone}")
            else:
                info.append(f"<strong>{distributor.businessname}</strong>: No users")

        self.message_user(
            request,
            format_html('<br>'.join(info)),
            messages.INFO
        )
    display_user_info.short_description = "Display user information"

    def save_model(self, request, obj, form, change):
        """Save the distributor and handle user relationships"""
        super().save_model(request, obj, form, change)

        # Save many-to-many relationships
        form.save_m2m()

    def save_related(self, request, form, formsets, change):
        """Save related objects"""
        super().save_related(request, form, formsets, change)

    def create_user_for_distributor(self, request, queryset):
        """Action to redirect to user creation page for selected distributor"""
        if queryset.count() != 1:
            self.message_user(
                request,
                'Please select exactly one distributor to create a user for.',
                messages.ERROR
            )
            return

        distributor = queryset.first()
        url = reverse('admin:chemsapp_distributor_create_user', args=[distributor.pk])
        return redirect(url)
    create_user_for_distributor.short_description = "Create new user for distributor"

    def create_user_view(self, request, distributor_id):
        """Custom view to create a new user and associate with distributor"""
        distributor = get_object_or_404(Distributor, pk=distributor_id)

        if request.method == 'POST':
            form = DistributorUserInlineForm(request.POST)
            if form.is_valid():
                user = form.save()
                distributor.users.add(user)

                # Send password reset email if requested
                if form.cleaned_data.get('send_password_reset') and user.email:
                    reset_form = PasswordResetForm({'email': user.email})
                    if reset_form.is_valid():
                        reset_form.save(
                            request=request,
                            use_https=request.is_secure(),
                            email_template_name='registration/password_reset_email.html',
                        )
                        messages.success(
                            request,
                            f'User "{user.username}" created and password reset email sent to {user.email}.'
                        )
                    else:
                        messages.success(
                            request,
                            f'User "{user.username}" created successfully.'
                        )
                else:
                    messages.success(
                        request,
                        f'User "{user.username}" created and associated with "{distributor.businessname}".'
                    )

                return redirect('admin:chemsapp_distributor_change', distributor.pk)
        else:
            form = DistributorUserInlineForm()

        context = {
            'title': f'Create User for {distributor.businessname}',
            'form': form,
            'distributor': distributor,
            'opts': self.model._meta,
            'has_permission': True,
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
            'site_url': self.admin_site.site_url,
        }
        return render(request, 'admin/chemsapp/distributor/create_user.html', context)


class CustomerContactInline(admin.TabularInline):
    model = CustomerContact
    extra = 1
    fields = ('name', 'role', 'email', 'phone', 'receive_report')


class CustomerProductVariantInline(admin.TabularInline):
    model = CustomerProductVariant
    extra = 1
    fields = ('product_variant', 'max_stock_level')


class CustomerAdmin(ImportExportModelAdmin):
    search_fields = ['address', 'businessName',]
    resource_class = CustomerResource
    inlines = [CustomerContactInline, CustomerProductVariantInline]
    filter_horizontal = ['products']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:customer_id>/wall-chart/',
                self.admin_site.admin_view(self.wall_chart_view),
                name='chemsapp_customer_wall_chart',
            ),
        ]
        return custom_urls + urls

    def wall_chart_view(self, request, customer_id):
        from django.http import HttpResponse
        from chemsapp.wall_chart_views import _build_wall_chart_pdf
        customer = get_object_or_404(Customer, pk=customer_id)
        products = customer.products.prefetch_related('safetyWears').order_by('name')
        pdf_bytes = _build_wall_chart_pdf(customer, products, request.build_absolute_uri('/'))
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="wall-chart-{customer_id}.pdf"'
        return response


class ProfileAdmin(admin.ModelAdmin):
    pass


class UserAdmin(admin.ModelAdmin):
    pass


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('code', 'size', 'pack_size', 'volume_litres', 'description', 'barcode', 'image')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'description':
            field.widget.attrs['rows'] = 2
            field.widget.attrs['style'] = 'width: 150px;'
        return field


class ProductAdmin(ImportExportModelAdmin):
    form = ProductForm
    search_fields = ['name',]
    readonly_fields = []
    resource_class = ProductResource
    inlines = [ProductVariantInline]
    filter_horizontal = ['safetyWears', 'subCategory', 'productCategory', 'sizes', 'fill_types']
    list_display = ['brand', 'name', 'get_categories', 'has_sds', 'has_pi_sheet', 'public']

    def get_categories(self, obj):
        return ', '.join(obj.productCategory.values_list('name', flat=True))
    get_categories.short_description = 'Category'

    def has_sds(self, obj):
        return bool(obj.sdsSheet)
    has_sds.boolean = True
    has_sds.short_description = 'SDS Attached'

    def has_pi_sheet(self, obj):
        return bool(obj.infoSheet)
    has_pi_sheet.boolean = True
    has_pi_sheet.short_description = 'PI Sheet Attached'


class FillTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'volume_litres', 'sort_order', 'is_active']
    list_editable = ['volume_litres', 'sort_order', 'is_active']


class VariantFillOverrideInline(admin.TabularInline):
    model = VariantFillOverride
    extra = 1


class ProductVariantAdmin(admin.ModelAdmin):
    """Standalone variant admin so cost-in-use overrides can be edited
    (inlines can't nest inside ProductVariantInline on the product page)."""
    search_fields = ['code', 'product__name', 'barcode']
    list_display = ['__str__', 'code', 'pack_size', 'volume_litres']
    list_select_related = ['product', 'size']
    inlines = [VariantFillOverrideInline]


#class ProductAddAdmin(ImportExportModelAdmin):
#    pass


#class ProductRemoveAdmin(ImportExportModelAdmin):
#    pass


class ProfileAdmin(ImportExportModelAdmin):
    pass


class CategoryAdmin(ImportExportModelAdmin):
    form = ProductCategoryForm
    filter_horizontal = ['products', 'relatedCategory']

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
    filter_horizontal = ['products']

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
admin.site.register(ProductVariant, ProductVariantAdmin)
admin.site.register(FillType, FillTypeAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(ProductCategory, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(NewsArticle, NewsPostAdmin)
admin.site.register(MarketCategory, MarketAdmin)
admin.site.register(MarketSector, SectorAdmin)
