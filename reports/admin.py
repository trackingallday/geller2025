from django.contrib import admin
from .models import (
    ReportType, ReportSection, Question, QuestionOption, 
    Report, Answer, ConditionalRule, ReportTypeCustomer, 
    QuestionTemplate
)


class ReportSectionInline(admin.TabularInline):
    model = ReportSection
    extra = 0
    fields = ('name', 'description', 'order')


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('question_text', 'question_type', 'section', 'order', 'is_required')
    readonly_fields = ('created_at',)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0
    fields = ('text', 'value', 'is_flag', 'order')


class ReportTypeCustomerInline(admin.TabularInline):
    model = ReportTypeCustomer
    extra = 0
    fields = ('customer', 'is_active', 'assigned_date', 'assigned_by')
    readonly_fields = ('assigned_date', 'assigned_by')


@admin.register(ReportType)
class ReportTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'auto_number_prefix', 'assigned_customers_count', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ReportSectionInline, QuestionInline, ReportTypeCustomerInline]
    
    def assigned_customers_count(self, obj):
        return obj.reporttypecustomer_set.count()
    assigned_customers_count.short_description = 'Assigned Customers'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReportSection)
class ReportSectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'order', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('report_type', 'order', 'name')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text_short', 'question_type', 'report_type', 'section', 'order', 'is_required')
    list_filter = ('question_type', 'report_type', 'section', 'is_required')
    search_fields = ('question_text', 'help_text')
    ordering = ('report_type', 'section', 'order')
    inlines = [QuestionOptionInline]
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question Text'


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question_short', 'value', 'is_flag', 'order')
    list_filter = ('is_flag', 'question__report_type')
    search_fields = ('text', 'value', 'question__question_text')
    ordering = ('question', 'order')
    
    def question_short(self, obj):
        return obj.question.question_text[:30] + "..." if len(obj.question.question_text) > 30 else obj.question.question_text
    question_short.short_description = 'Question'


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ('question', 'text_answer', 'file_answer', 'signature_answer')
    readonly_fields = ('question',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'report_type', 'customer', 'distributor', 'status', 'prepared_by', 'inspection_date')
    list_filter = ('status', 'report_type', 'inspection_date', 'created_at')
    search_fields = ('document_number', 'customer__businessName', 'distributor__businessName', 'store_compliance_manager')
    readonly_fields = ('document_number', 'created_at', 'updated_at')
    inlines = [AnswerInline]
    
    fieldsets = (
        ('Report Information', {
            'fields': ('document_number', 'report_type', 'customer', 'distributor')
        }),
        ('Report Details', {
            'fields': ('store_compliance_manager', 'inspection_date', 'prepared_by')
        }),
        ('Status', {
            'fields': ('status', 'submitted_at', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('report', 'question_short', 'answer_display', 'created_at')
    list_filter = ('report__report_type', 'question__question_type', 'created_at')
    search_fields = ('report__document_number', 'question__question_text', 'text_answer')
    readonly_fields = ('created_at', 'updated_at')
    
    def question_short(self, obj):
        return obj.question.question_text[:40] + "..." if len(obj.question.question_text) > 40 else obj.question.question_text
    question_short.short_description = 'Question'
    
    def answer_display(self, obj):
        return obj.get_display_value()
    answer_display.short_description = 'Answer'


@admin.register(ConditionalRule)
class ConditionalRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'trigger_question_short', 'trigger_value', 'action', 'target_question_short')
    list_filter = ('report_type', 'action')
    search_fields = ('name', 'trigger_question__question_text', 'target_question__question_text')
    
    def trigger_question_short(self, obj):
        return obj.trigger_question.question_text[:30] + "..." if len(obj.trigger_question.question_text) > 30 else obj.trigger_question.question_text
    trigger_question_short.short_description = 'Trigger Question'
    
    def target_question_short(self, obj):
        return obj.target_question.question_text[:30] + "..." if len(obj.target_question.question_text) > 30 else obj.target_question.question_text
    target_question_short.short_description = 'Target Question'


@admin.register(ReportTypeCustomer)
class ReportTypeCustomerAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'customer_name', 'customer_email', 'assigned_date', 'is_active', 'assigned_by')
    list_filter = ('report_type', 'assigned_date', 'is_active')
    search_fields = ('customer__businessName', 'customer__email', 'report_type__name')
    readonly_fields = ('assigned_date', 'assigned_by')
    date_hierarchy = 'assigned_date'
    
    def customer_name(self, obj):
        return obj.customer.businessName or obj.customer.get_full_name()
    customer_name.short_description = 'Customer Name'
    customer_name.admin_order_field = 'customer__businessName'
    
    def customer_email(self, obj):
        return obj.customer.email
    customer_email.short_description = 'Customer Email'
    customer_email.admin_order_field = 'customer__email'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'question_type', 'category', 'usage_count', 'created_by', 'created_at')
    list_filter = ('question_type', 'category', 'created_at', 'created_by')
    search_fields = ('name', 'question_text')
    readonly_fields = ('usage_count', 'created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'category')
        }),
        ('Question Content', {
            'fields': ('question_text', 'question_type', 'help_text', 'is_required_default')
        }),
        ('Configuration', {
            'fields': ('template_options',),
            'classes': ('collapse',)
        }),
        ('Usage & Metadata', {
            'fields': ('usage_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
