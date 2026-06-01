from django.contrib import admin
from .models import Ticket, TicketReply, TicketImage


class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1
    readonly_fields = ('created_at',)


class TicketImageInline(admin.TabularInline):
    model = TicketImage
    extra = 0
    readonly_fields = ('uploaded_at',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'ticket_type', 'customer', 'created_by', 'assigned_to', 'status', 'created_at']
    list_filter = ['ticket_type', 'status', 'created_at']
    search_fields = ['subject', 'body', 'customer__businessName', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'source_report']
    inlines = [TicketReplyInline, TicketImageInline]
