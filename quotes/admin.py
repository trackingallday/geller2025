from django.contrib import admin
from django.utils.html import format_html

from .models import Quote, QuoteLine


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 1
    fields = ('product_variant', 'price', 'sort_order', 'product_name', 'product_code', 'cost_in_use')
    readonly_fields = ('product_name', 'product_code', 'cost_in_use')


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    change_list_template = 'admin/quotes/quote/change_list.html'
    list_display = ['quote_number', 'company_name', 'contact_name', 'date', 'created_by', 'pdf_link']
    list_filter = ['date']
    search_fields = ['quote_number', 'company_name', 'contact_name']
    readonly_fields = ['quote_number', 'date', 'pdf', 'created_at', 'updated_at']
    inlines = [QuoteLineInline]

    def save_related(self, request, form, formsets, change):
        """Admin edits deliberately re-freeze snapshots from current product
        data and regenerate the PDF (mirrors CustomerOrderAdmin)."""
        super().save_related(request, form, formsets, change)
        from .services import refresh_line_snapshots
        from .utils import QuotePDFGenerator
        quote = form.instance
        refresh_line_snapshots(quote)
        QuotePDFGenerator(quote).generate_and_save()

    def pdf_link(self, obj):
        if obj.pdf:
            return format_html('<a href="{}">View PDF</a>', obj.pdf.url)
        return '-'
    pdf_link.short_description = 'PDF'
