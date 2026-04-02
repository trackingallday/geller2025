from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
import json
from .models import (
    ReportType, ReportSection, Question, QuestionOption,
    Report, Answer, AnswerAttachment, ConditionalRule, ReportTypeCustomer, ReportTypeDistributor,
    QuestionTemplate, ComplianceManager
)
from chemsapp.models import Customer



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
    fields = ('text', 'value', 'is_flag', 'badge_type', 'order')


class ReportTypeCustomerInline(admin.TabularInline):
    model = ReportTypeCustomer
    extra = 0
    fields = ('customer', 'is_active', 'assigned_date', 'assigned_by')
    readonly_fields = ('assigned_date', 'assigned_by')


class ReportTypeDistributorInline(admin.TabularInline):
    model = ReportTypeDistributor
    extra = 0
    fields = ('distributor', 'is_active', 'assigned_date', 'assigned_by')
    readonly_fields = ('assigned_date', 'assigned_by')


@admin.register(ReportType)
class ReportTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'auto_number_prefix', 'assigned_customers_count', 'assigned_distributors_count', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ReportSectionInline, QuestionInline, ReportTypeCustomerInline, ReportTypeDistributorInline]
    
    def assigned_customers_count(self, obj):
        return obj.customer_assignments.count()
    assigned_customers_count.short_description = 'Assigned Customers'

    def assigned_distributors_count(self, obj):
        return obj.distributor_assignments.count()
    assigned_distributors_count.short_description = 'Assigned Distributors'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'assign/',
                self.admin_site.admin_view(self.assign_view),
                name='reports_assign'
            ),
            path(
                'assign/toggle/',
                self.admin_site.admin_view(self.assign_toggle),
                name='reports_assign_toggle'
            ),
        ]
        return custom_urls + urls

    def assign_view(self, request):
        customers = Customer.objects.select_related('user').order_by('businessName')
        report_types = ReportType.objects.filter(is_active=True).order_by('name')
        active_assignments = list(
            ReportTypeCustomer.objects.filter(is_active=True).values(
                'customer_id', 'report_type_id', 'report_type__name'
            )
        )
        total_assignments = len(active_assignments)
        context = {
            **self.admin_site.each_context(request),
            'title': 'Assign Report Types',
            'customers': customers,
            'report_types': report_types,
            'active_assignments': active_assignments,
            'total_assignments': total_assignments,
        }
        return render(request, 'admin/reports/assign_report_types.html', context)

    def assign_toggle(self, request):
        if request.method != 'POST':
            return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
        try:
            data = json.loads(request.body)
            customer_id = int(data['customer_id'])
            report_type_id = int(data['report_type_id'])
            active = bool(data['active'])
        except (KeyError, ValueError, json.JSONDecodeError):
            return JsonResponse({'ok': False, 'error': 'Invalid data'}, status=400)

        try:
            customer = Customer.objects.get(pk=customer_id)
            report_type = ReportType.objects.get(pk=report_type_id)
        except (Customer.DoesNotExist, ReportType.DoesNotExist):
            return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)

        with transaction.atomic():
            assignment, created = ReportTypeCustomer.objects.get_or_create(
                report_type=report_type,
                customer=customer,
                defaults={'assigned_by': request.user, 'is_active': active}
            )
            if not created:
                assignment.is_active = active
                if active:
                    assignment.assigned_by = request.user
                assignment.save(update_fields=['is_active', 'assigned_by'])

        return JsonResponse({'ok': True})


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
    list_display = ('text', 'question_short', 'value', 'is_flag', 'badge_type', 'order')
    list_filter = ('is_flag', 'badge_type', 'question__report_type')
    search_fields = ('text', 'value', 'question__question_text')
    ordering = ('question', 'order')
    fields = ('question', 'text', 'value', 'is_flag', 'badge_type', 'additional_instructions', 'attached_pdf', 'order')

    def question_short(self, obj):
        return obj.question.question_text[:30] + "..." if len(obj.question.question_text) > 30 else obj.question.question_text
    question_short.short_description = 'Question'


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ('question', 'text_answer', 'file_answer', 'file_image_preview', 'signature_answer', 'signature_image_preview', 'attachment', 'attachment_image_preview', 'all_attachments_preview')
    readonly_fields = ('question', 'file_image_preview', 'signature_image_preview', 'attachment_image_preview', 'all_attachments_preview')

    def file_image_preview(self, obj):
        if obj.file_answer:
            file_url = obj.file_answer.url
            file_name = obj.file_answer.name.lower()
            if any(ext in file_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                return format_html(
                    '<img src="{}" style="max-height: 100px; max-width: 150px;" /><br><small><a href="{}" target="_blank">{}</a></small>',
                    file_url, file_url, obj.file_answer.name
                )
            else:
                return format_html('<a href="{}" target="_blank">{}</a>', file_url, obj.file_answer.name)
        return "No file"
    file_image_preview.short_description = 'File Preview'

    def signature_image_preview(self, obj):
        if obj.signature_answer:
            file_url = obj.signature_answer.url
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" /><br><small><a href="{}" target="_blank">{}</a></small>',
                file_url, file_url, obj.signature_answer.name
            )
        return "No signature"
    signature_image_preview.short_description = 'Signature Preview'

    def attachment_image_preview(self, obj):
        if obj.attachment:
            file_url = obj.attachment.url
            file_name = obj.attachment.name.lower()
            if any(ext in file_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                return format_html(
                    '<img src="{}" style="max-height: 100px; max-width: 150px;" /><br><small><a href="{}" target="_blank">{}</a></small>',
                    file_url, file_url, obj.attachment.name
                )
            else:
                return format_html('<a href="{}" target="_blank">{}</a>', file_url, obj.attachment.name)
        return "No attachment"
    attachment_image_preview.short_description = 'Attachment Preview'

    def all_attachments_preview(self, obj):
        attachments = obj.attachments.all()
        if not attachments:
            return "No attachments"
        html_parts = []
        for att in attachments:
            file_url = att.file.url
            file_name = att.file.name.lower()
            if any(ext in file_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                html_parts.append(
                    '<img src="{}" style="max-height: 100px; max-width: 150px;" /><br><small><a href="{}" target="_blank">{}</a></small>'.format(
                        file_url, file_url, att.file.name
                    )
                )
            else:
                html_parts.append('<a href="{}" target="_blank">{}</a>'.format(file_url, att.file.name))
        return format_html('<br>'.join(html_parts))
    all_attachments_preview.short_description = 'Attachments'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'report_type', 'customer', 'distributor', 'compliance_manager_display', 'status', 'prepared_by', 'inspection_date', 'images_count', 'pdf_status', 'pdf_download_link', 'completed_reports_link')
    list_filter = ('status', 'report_type', 'inspection_date', 'created_at', 'pdf_needs_regeneration', 'compliance_manager')
    search_fields = ('document_number', 'customer__businessName', 'distributor__businessname', 'store_compliance_manager', 'compliance_manager__name')
    readonly_fields = ('document_number', 'created_at', 'updated_at', 'pdf_generated_at', 'pdf_download_button', 'regenerate_pdf_button', 'images_summary', 'completed_reports_view_button')
    inlines = [AnswerInline]

    actions = ['generate_pdfs', 'regenerate_pdfs']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('document_number', 'report_type', 'customer', 'distributor', 'completed_reports_view_button')
        }),
        ('Report Details', {
            'fields': ('compliance_manager', 'store_compliance_manager', 'inspection_date', 'prepared_by')
        }),
        ('Status', {
            'fields': ('status', 'submitted_at', 'reviewed_by', 'reviewed_at')
        }),
        ('PDF Generation', {
            'fields': ('pdf_file', 'pdf_download_button', 'regenerate_pdf_button', 'pdf_generated_at', 'pdf_needs_regeneration'),
            'classes': ('collapse',)
        }),
        ('Images Summary', {
            'fields': ('images_summary',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def compliance_manager_display(self, obj):
        """Display the compliance manager name from either source"""
        return obj.compliance_manager_name or '-'
    compliance_manager_display.short_description = 'Compliance Manager'
    compliance_manager_display.admin_order_field = 'compliance_manager__name'

    def pdf_status(self, obj):
        if obj.pdf_file:
            if obj.pdf_needs_regeneration:
                return "Available (needs regeneration)"
            else:
                return "Available"
        else:
            return "Not generated"
    pdf_status.short_description = 'PDF Status'

    def pdf_download_link(self, obj):
        if obj.pdf_file:
            download_url = reverse('admin:reports_report_pdf_download', args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank" class="button">Download PDF</a>',
                download_url
            )
        else:
            return "No PDF"
    pdf_download_link.short_description = 'Download'

    def completed_reports_link(self, obj):
        """Link to view this report in the Completed Reports interface"""
        completed_url = reverse('reports:completed_report_detail', args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" class="button">View Report</a>',
            completed_url
        )
    completed_reports_link.short_description = 'View'

    def pdf_download_button(self, obj):
        if obj.pdf_file:
            download_url = reverse('admin:reports_report_pdf_download', args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank" class="button default">Download PDF Report</a><br><br>'
                '<small>File: {}</small>',
                download_url,
                obj.pdf_file.name
            )
        else:
            return format_html(
                '<em>No PDF generated yet.</em><br>'
                '<small>Save the report and generate PDF using the admin actions above.</small>'
            )
    pdf_download_button.short_description = 'PDF Download'

    def regenerate_pdf_button(self, obj):
        regenerate_url = reverse('admin:reports_report_regenerate_pdf', args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" onclick="return confirm(\'Regenerate PDF for this report?\')">Regenerate PDF</a>',
            regenerate_url
        )
    regenerate_pdf_button.short_description = 'Regenerate PDF'

    def completed_reports_view_button(self, obj):
        """Large button to view report in Completed Reports interface"""
        completed_url = reverse('reports:completed_report_detail', args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" class="button default" style="font-size: 14px; padding: 10px 20px;">'
            '<strong>📋 View in Completed Reports Interface</strong></a><br><br>'
            '<small>Opens the report in the customer-facing completed reports view</small>',
            completed_url
        )
    completed_reports_view_button.short_description = 'Completed Reports View'

    def generate_pdfs(self, request, queryset):
        generated_count = 0
        error_count = 0

        for report in queryset:
            try:
                if report.generate_pdf():
                    generated_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(request, f"Error generating PDF for {report.document_number}: {str(e)}", level='ERROR')

        if generated_count > 0:
            self.message_user(request, f"Successfully generated {generated_count} PDF(s).")
        if error_count > 0:
            self.message_user(request, f"Failed to generate {error_count} PDF(s).", level='WARNING')

    generate_pdfs.short_description = "Generate PDFs for selected reports"

    def regenerate_pdfs(self, request, queryset):
        # Force regeneration by marking all as needing regeneration
        queryset.update(pdf_needs_regeneration=True)
        self.generate_pdfs(request, queryset)

    regenerate_pdfs.short_description = "Regenerate PDFs for selected reports"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/download-pdf/', self.pdf_download_view, name='reports_report_pdf_download'),
            path('<int:object_id>/regenerate-pdf/', self.regenerate_pdf_view, name='reports_report_regenerate_pdf'),
        ]
        return custom_urls + urls

    def pdf_download_view(self, request, object_id):
        import mimetypes
        import os

        # Get the report object
        report = get_object_or_404(Report, pk=object_id)

        # Check if PDF exists
        if not report.pdf_file:
            # Try to generate PDF if it doesn't exist
            if report.generate_pdf():
                report.refresh_from_db()
            else:
                raise Http404("PDF not available")

        # Check if file exists on disk
        if not report.pdf_file or not os.path.exists(report.pdf_file.path):
            raise Http404("PDF file not found")

        # Serve the PDF file
        try:
            with open(report.pdf_file.path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{report.document_number}.pdf"'
                return response
        except IOError:
            raise Http404("Error reading PDF file")

    def regenerate_pdf_view(self, request, object_id):

        # Get the report object
        report = get_object_or_404(Report, pk=object_id)

        try:
            # Force regeneration
            report.pdf_needs_regeneration = True
            success = report.generate_pdf()

            if success:
                messages.success(request, f'PDF successfully regenerated for report {report.document_number}')
            else:
                messages.error(request, f'Failed to regenerate PDF for report {report.document_number}')

        except Exception as e:
            messages.error(request, f'Error regenerating PDF: {str(e)}')

        # Redirect back to the report detail page
        return HttpResponseRedirect(reverse('admin:reports_report_change', args=[object_id]))

    def images_count(self, obj):
        """Count total images/files in the report"""
        from django.db.models import Q
        count = obj.answers.filter(
            Q(file_answer__isnull=False) |
            Q(signature_answer__isnull=False) |
            Q(attachment__isnull=False) |
            Q(attachments__isnull=False)
        ).distinct().count()
        if count > 0:
            return f"{count} 📷"
        return "—"
    images_count.short_description = 'Images'
    images_count.admin_order_field = 'answers__file_answer'

    def images_summary(self, obj):
        """Show detailed summary of all images in the report"""
        from django.db.models import Q

        answers_with_files = obj.answers.filter(
            Q(file_answer__isnull=False) |
            Q(signature_answer__isnull=False) |
            Q(attachment__isnull=False) |
            Q(attachments__isnull=False)
        ).distinct().select_related('question').prefetch_related('attachments')

        if not answers_with_files:
            return format_html('<em>No images in this report</em>')

        html_parts = ['<div style="max-width: 800px;">']
        html_parts.append('<h4>Images in this Report:</h4>')

        for answer in answers_with_files:
            html_parts.append(f'<div style="margin-bottom: 20px; border: 1px solid #ddd; padding: 10px;">')
            html_parts.append(f'<strong>Question:</strong> {answer.question.question_text[:80]}...<br>')

            if answer.file_answer:
                file_url = answer.file_answer.url
                file_name = answer.file_answer.name.lower()
                if any(ext in file_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    html_parts.append(f'<strong>File Answer:</strong><br>')
                    html_parts.append(f'<img src="{file_url}" style="max-height: 150px; max-width: 200px; margin: 5px 0;" /><br>')
                    html_parts.append(f'<small><a href="{file_url}" target="_blank">{answer.file_answer.name}</a></small><br>')
                else:
                    html_parts.append(f'<strong>File Answer:</strong> <a href="{file_url}" target="_blank">{answer.file_answer.name}</a><br>')

            if answer.signature_answer:
                sig_url = answer.signature_answer.url
                html_parts.append(f'<strong>Signature:</strong><br>')
                html_parts.append(f'<img src="{sig_url}" style="max-height: 100px; max-width: 200px; margin: 5px 0;" /><br>')
                html_parts.append(f'<small><a href="{sig_url}" target="_blank">{answer.signature_answer.name}</a></small><br>')

            if answer.attachment:
                att_url = answer.attachment.url
                att_name = answer.attachment.name.lower()
                if any(ext in att_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    html_parts.append(f'<strong>Attachment (legacy):</strong><br>')
                    html_parts.append(f'<img src="{att_url}" style="max-height: 150px; max-width: 200px; margin: 5px 0;" /><br>')
                    html_parts.append(f'<small><a href="{att_url}" target="_blank">{answer.attachment.name}</a></small><br>')
                else:
                    html_parts.append(f'<strong>Attachment (legacy):</strong> <a href="{att_url}" target="_blank">{answer.attachment.name}</a><br>')

            for i, att in enumerate(answer.attachments.all(), 1):
                att_url = att.file.url
                att_name = att.file.name.lower()
                if any(ext in att_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    html_parts.append(f'<strong>Attachment {i}:</strong><br>')
                    html_parts.append(f'<img src="{att_url}" style="max-height: 150px; max-width: 200px; margin: 5px 0;" /><br>')
                    html_parts.append(f'<small><a href="{att_url}" target="_blank">{att.file.name}</a></small><br>')
                else:
                    html_parts.append(f'<strong>Attachment {i}:</strong> <a href="{att_url}" target="_blank">{att.file.name}</a><br>')

            html_parts.append('</div>')

        html_parts.append('</div>')
        return format_html(''.join(html_parts))
    images_summary.short_description = 'All Images in Report'


class AnswerAttachmentInline(admin.TabularInline):
    model = AnswerAttachment
    extra = 1
    fields = ('file', 'caption', 'file_preview')
    readonly_fields = ('file_preview',)

    def file_preview(self, obj):
        if obj.file:
            file_url = obj.file.url
            file_name = obj.file.name.lower()
            if any(ext in file_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                return format_html(
                    '<img src="{}" style="max-height: 100px; max-width: 150px;" /><br><small><a href="{}" target="_blank">{}</a></small>',
                    file_url, file_url, obj.file.name
                )
            else:
                return format_html('<a href="{}" target="_blank">{}</a>', file_url, obj.file.name)
        return "No file"
    file_preview.short_description = 'Preview'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('report', 'question_short', 'answer_display', 'has_images', 'created_at')
    list_filter = ('report__report_type', 'question__question_type', 'created_at')
    search_fields = ('report__document_number', 'question__question_text', 'text_answer')
    readonly_fields = ('created_at', 'updated_at', 'file_image_preview', 'signature_image_preview', 'attachment_image_preview')
    inlines = [AnswerAttachmentInline]

    fieldsets = (
        ('Answer Information', {
            'fields': ('report', 'question', 'text_answer', 'date_answer', 'number_answer')
        }),
        ('File Uploads', {
            'fields': ('file_answer', 'file_image_preview', 'signature_answer', 'signature_image_preview', 'attachment', 'attachment_image_preview')
        }),
        ('Selected Options', {
            'fields': ('selected_options',)
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def question_short(self, obj):
        return obj.question.question_text[:40] + "..." if len(obj.question.question_text) > 40 else obj.question.question_text
    question_short.short_description = 'Question'

    def answer_display(self, obj):
        return obj.get_display_value()
    answer_display.short_description = 'Answer'

    def has_images(self, obj):
        has_files = bool(obj.file_answer or obj.signature_answer or obj.attachment or obj.attachments.exists())
        return "✓" if has_files else "—"
    has_images.short_description = 'Images'
    has_images.admin_order_field = 'file_answer'

    def file_image_preview(self, obj):
        if obj.file_answer:
            file_url = obj.file_answer.url
            file_name = obj.file_answer.name.lower()
            if any(ext in file_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                return format_html(
                    '<img src="{}" style="max-height: 200px; max-width: 300px; border: 1px solid #ddd;" /><br><small><a href="{}" target="_blank">{}</a></small>',
                    file_url, file_url, obj.file_answer.name
                )
            else:
                return format_html('<a href="{}" target="_blank">{}</a>', file_url, obj.file_answer.name)
        return "No file"
    file_image_preview.short_description = 'File Preview'

    def signature_image_preview(self, obj):
        if obj.signature_answer:
            file_url = obj.signature_answer.url
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px; border: 1px solid #ddd;" /><br><small><a href="{}" target="_blank">{}</a></small>',
                file_url, file_url, obj.signature_answer.name
            )
        return "No signature"
    signature_image_preview.short_description = 'Signature Preview'

    def attachment_image_preview(self, obj):
        if obj.attachment:
            file_url = obj.attachment.url
            file_name = obj.attachment.name.lower()
            if any(ext in file_name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                return format_html(
                    '<img src="{}" style="max-height: 200px; max-width: 300px; border: 1px solid #ddd;" /><br><small><a href="{}" target="_blank">{}</a></small>',
                    file_url, file_url, obj.attachment.name
                )
            else:
                return format_html('<a href="{}" target="_blank">{}</a>', file_url, obj.attachment.name)
        return "No attachment"
    attachment_image_preview.short_description = 'Attachment Preview'


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


@admin.register(ReportTypeDistributor)
class ReportTypeDistributorAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'distributor_name', 'distributor_email', 'assigned_date', 'is_active', 'assigned_by')
    list_filter = ('report_type', 'assigned_date', 'is_active')
    search_fields = ('distributor__businessname', 'distributor__users__email', 'report_type__name')
    readonly_fields = ('assigned_date', 'assigned_by')
    date_hierarchy = 'assigned_date'

    def distributor_name(self, obj):
        first_user = obj.distributor.users.first()
        return obj.distributor.businessname or (first_user.get_full_name() if first_user else '')
    distributor_name.short_description = 'Distributor Name'
    distributor_name.admin_order_field = 'distributor__businessname'

    def distributor_email(self, obj):
        first_user = obj.distributor.users.first()
        return first_user.email if first_user else ''
    distributor_email.short_description = 'Distributor Email'

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


@admin.register(ComplianceManager)
class ComplianceManagerAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_name', 'phone_number', 'created_at')
    list_filter = ('customer', 'created_at')
    search_fields = ('name', 'phone_number', 'customer__businessName')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Manager Information', {
            'fields': ('customer', 'name', 'phone_number')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def customer_name(self, obj):
        return obj.customer.businessName
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'customer__businessName'


