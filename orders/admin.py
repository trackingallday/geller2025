from django.contrib import admin
from django.urls import path
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.html import format_html
from .models import CustomerOrder, OrderLineItem


class OrderLineItemInline(admin.TabularInline):
    model = OrderLineItem
    extra = 1
    fields = ('product_variant', 'quantity')


@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'date', 'fulfilment_status', 'submitted', 'pdf_link']
    list_filter = ['fulfilment_status', 'submitted', 'date']
    search_fields = ['order_number', 'customer__businessName']
    readonly_fields = ['order_number', 'date', 'created_at', 'updated_at', 'pdf']
    inlines = [OrderLineItemInline]
    change_form_template = 'orders/admin/customerorder_change_form.html'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.submitted:
            return self.readonly_fields + ['submitted']
        return self.readonly_fields

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/submit/', self.admin_site.admin_view(self.submit_order_view), name='orders_customerorder_submit'),
        ]
        return custom + urls

    def submit_order_view(self, request, pk):
        order = get_object_or_404(CustomerOrder, pk=pk)
        if order.submitted:
            messages.warning(request, f'Order {order.order_number} has already been submitted.')
        else:
            order.submitted = True
            order.save()
            from .utils import OrderPDFGenerator
            OrderPDFGenerator(order).generate_and_save()
            messages.success(request, f'Order {order.order_number} submitted and PDF generated.')
        return redirect('admin:orders_customerorder_change', pk)

    def save_related(self, request, form, formsets, change):
        """Generate PDF if submitted was ticked manually via the checkbox."""
        super().save_related(request, form, formsets, change)
        instance = form.instance
        was_submitted = form.initial.get('submitted', False)
        if instance.submitted and not was_submitted:
            from .utils import OrderPDFGenerator
            OrderPDFGenerator(instance).generate_and_save()

    def pdf_link(self, obj):
        if obj.pdf:
            return format_html('<a href="{}">View PDF</a>', obj.pdf.url)
        return '-'
    pdf_link.short_description = 'PDF'
