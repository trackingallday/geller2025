from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from chemsapp.models import Customer, Distributor, MyBaseModel
import uuid


QUESTION_TYPES = [
    ('text', 'Text Input'),
    ('textarea', 'Long Text'),
    ('select', 'Select Dropdown'),
    ('radio', 'Multiple Choice (Radio)'),
    ('checkbox', 'Multiple Choice (Checkbox)'),
    ('yesno', 'Yes/No'),
    ('file', 'File Upload'),
    ('signature', 'Digital Signature'),
    ('date', 'Date'),
    ('number', 'Number'),
]

REPORT_STATUS = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

# Status constants for easy reference
class ReportStatus:
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class ReportType(MyBaseModel):
    """Template for different types of reports (Monthly Audit, Equipment Check, etc.)"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    auto_number_prefix = models.CharField(max_length=10, blank=True, null=True, help_text="Prefix for auto-generated document numbers")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_next_document_number(self):
        """Generate the next document number for this report type"""
        if self.auto_number_prefix:
            last_report = Report.objects.filter(
                report_type=self,
                document_number__startswith=self.auto_number_prefix
            ).order_by('-document_number').first()
            
            if last_report:
                try:
                    last_num = int(last_report.document_number.replace(self.auto_number_prefix, ''))
                    return f"{self.auto_number_prefix}{last_num + 1:04d}"
                except ValueError:
                    return f"{self.auto_number_prefix}0001"
            else:
                return f"{self.auto_number_prefix}0001"
        else:
            return str(uuid.uuid4())[:8].upper()
    
    def is_available_to_customer(self, customer):
        """Check if this report type is available to the specified customer"""
        return self.customer_assignments.filter(
            customer=customer, 
            is_active=True
        ).exists()
    
    def get_assigned_customers(self):
        """Get all customers assigned to this report type"""
        return Customer.objects.filter(
            report_type_assignments__report_type=self,
            report_type_assignments__is_active=True
        )
    
    def assign_to_customer(self, customer, assigned_by=None, notes=None):
        """Assign this report type to a customer"""
        assignment, created = ReportTypeCustomer.objects.get_or_create(
            report_type=self,
            customer=customer,
            defaults={
                'assigned_by': assigned_by,
                'notes': notes
            }
        )
        if not created and not assignment.is_active:
            assignment.is_active = True
            assignment.assigned_by = assigned_by
            assignment.notes = notes
            assignment.save()
        return assignment

    def is_available_to_distributor(self, distributor):
        """Check if this report type is available to the specified distributor"""
        return self.distributor_assignments.filter(
            distributor=distributor,
            is_active=True
        ).exists()

    def get_assigned_distributors(self):
        """Get all distributors assigned to this report type"""
        return Distributor.objects.filter(
            report_type_assignments__report_type=self,
            report_type_assignments__is_active=True
        )

    def assign_to_distributor(self, distributor, assigned_by=None, notes=None):
        """Assign this report type to a distributor"""
        assignment, created = ReportTypeDistributor.objects.get_or_create(
            report_type=self,
            distributor=distributor,
            defaults={
                'assigned_by': assigned_by,
                'notes': notes
            }
        )
        if not created and not assignment.is_active:
            assignment.is_active = True
            assignment.assigned_by = assigned_by
            assignment.notes = notes
            assignment.save()
        return assignment


class ReportSection(MyBaseModel):
    """Groups related questions within a report type"""
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.report_type.name} - {self.name}"


class Question(MyBaseModel):
    """Individual question within a report"""
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='questions')
    section = models.ForeignKey(ReportSection, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    help_text = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    # For conditional logic
    parent_question = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='child_questions')
    show_when_parent_values = models.JSONField(default=list, blank=True, help_text="Show this question when parent has any of these values")
    
    # Backward compatibility field (deprecated)
    show_when_parent_value = models.CharField(max_length=255, blank=True, null=True, help_text="DEPRECATED: Use show_when_parent_values instead")
    
    class Meta:
        ordering = ['order', 'question_text']
    
    def __str__(self):
        return f"{self.report_type.name} - {self.question_text[:50]}..."
    
    def get_show_when_values(self):
        """Get the list of values that should trigger this question to show"""
        if self.show_when_parent_values:
            return self.show_when_parent_values
        elif self.show_when_parent_value:
            # Backward compatibility - convert single value to list
            return [self.show_when_parent_value]
        return []
    
    def set_show_when_values(self, values):
        """Set the list of values that should trigger this question to show"""
        if isinstance(values, (list, tuple)):
            self.show_when_parent_values = list(values)
        else:
            # Single value provided
            self.show_when_parent_values = [values]
        # Clear the deprecated field
        self.show_when_parent_value = None


class QuestionOption(MyBaseModel):
    """Options for select/radio/checkbox questions"""

    BADGE_TYPE_CHOICES = [
        ('default', 'Default (No Badge)'),
        ('pass', 'Pass (Green)'),
        ('fail', 'Fail (Red)'),
        ('warning', 'Warning (Orange)'),
        ('info', 'Info (Blue)'),
        ('data', 'Data (Gray)'),
    ]

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    is_flag = models.BooleanField(default=False, help_text="Mark this option as requiring attention (will appear in Flagged Items page)")
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPE_CHOICES, default='default', help_text="Badge color to display in PDF report")
    additional_instructions = models.TextField(blank=True, null=True)
    attached_pdf = models.FileField(upload_to='report_attachments/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'text']

    def __str__(self):
        return f"{self.question.question_text[:30]}... - {self.text}"


class Report(MyBaseModel):
    """Instance of a filled report"""
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='reports')
    document_number = models.CharField(max_length=50, unique=True)
    
    # Link to existing customer/distributor system
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reports', blank=True, null=True)
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE, related_name='reports', blank=True, null=True)
    
    # Report metadata
    compliance_manager = models.ForeignKey('ComplianceManager', on_delete=models.SET_NULL, blank=True, null=True, related_name='reports', help_text="Select a compliance manager from the customer's list")
    store_compliance_manager = models.CharField(max_length=255, blank=True, null=True, help_text="Manual entry for compliance manager name (used if no compliance manager is selected)")
    inspection_date = models.DateField(default=timezone.now)
    prepared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_prepared')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='draft')
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='reports_reviewed')
    reviewed_at = models.DateTimeField(blank=True, null=True)

    # PDF Generation
    pdf_file = models.FileField(upload_to='report_pdfs/', blank=True, null=True, help_text="Generated PDF of the report")
    pdf_generated_at = models.DateTimeField(blank=True, null=True)
    pdf_needs_regeneration = models.BooleanField(default=True, help_text="True if PDF needs to be regenerated due to changes")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document_number} - {self.report_type.name}"
    
    def save(self, *args, **kwargs):
        if not self.document_number:
            self.document_number = self.report_type.get_next_document_number()

        # Check if this is an update and if key fields have changed
        if self.pk:
            old_instance = Report.objects.get(pk=self.pk)
            # Mark PDF for regeneration if key fields changed
            if (old_instance.status != self.status or
                old_instance.inspection_date != self.inspection_date or
                old_instance.compliance_manager != self.compliance_manager or
                old_instance.store_compliance_manager != self.store_compliance_manager):
                self.pdf_needs_regeneration = True

        super().save(*args, **kwargs)

    @property
    def compliance_manager_name(self):
        """Get the compliance manager name from either the ForeignKey or the text field"""
        if self.compliance_manager:
            return self.compliance_manager.name
        elif self.store_compliance_manager:
            return self.store_compliance_manager
        return None

    def log_all_images(self):
        """Log all images in this report to console"""
        import logging
        logger = logging.getLogger('django')

        logger.info(f"=== IMAGE LOGGING FOR REPORT: {self.document_number} ===")

        # Get all answers with images
        answers_with_files = self.answers.filter(
            models.Q(file_answer__isnull=False) |
            models.Q(signature_answer__isnull=False) |
            models.Q(attachment__isnull=False) |
            models.Q(attachments__isnull=False)
        ).distinct()

        if not answers_with_files.exists():
            logger.info(f"Report {self.document_number}: No images found")
            return

        for answer in answers_with_files:
            logger.info(f"Question: {answer.question.question_text[:50]}...")

            if answer.file_answer:
                logger.info(f"  - File Answer: {answer.file_answer.name}")
                logger.info(f"    URL: {answer.file_answer.url}")

            if answer.signature_answer:
                logger.info(f"  - Signature: {answer.signature_answer.name}")
                logger.info(f"    URL: {answer.signature_answer.url}")

            if answer.attachment:
                logger.info(f"  - Attachment (legacy): {answer.attachment.name}")
                logger.info(f"    URL: {answer.attachment.url}")

            for att in answer.attachments.all():
                logger.info(f"  - Attachment: {att.file.name}")
                logger.info(f"    URL: {att.file.url}")

        logger.info(f"=== END IMAGE LOGGING FOR REPORT: {self.document_number} ===")

    def get_all_answers_with_images(self):
        """Get all answers for this report, organized by section with image handling
        Orders sections by their order field (0, 1, 2...) and questions within sections by their order field
        """
        from collections import OrderedDict

        answers_by_section = OrderedDict()

        # Order answers by section order (ascending: 0, 1, 2...), then by question order
        ordered_answers = self.answers.select_related(
            'question',
            'question__section'
        ).prefetch_related('selected_options', 'attachments').order_by(
            'question__section__order',  # Section order: 0, 1, 2, 3...
            'question__order'  # Then question order within section: 0, 1, 2, 3...
        )

        for answer in ordered_answers:
            section_name = answer.question.section.name if answer.question.section else "General"

            if section_name not in answers_by_section:
                answers_by_section[section_name] = []

            answer_data = {
                'question': answer.question,
                'answer': answer,
                'display_value': answer.get_display_value(),
                'has_image': bool(answer.file_answer or answer.signature_answer or answer.attachment or answer.attachments.exists()),
                'images': []
            }

            # Collect all images for this answer
            if answer.file_answer and self._is_image_file(answer.file_answer.name):
                answer_data['images'].append(answer.file_answer)
            if answer.signature_answer:
                answer_data['images'].append(answer.signature_answer)
            if answer.attachment and self._is_image_file(answer.attachment.name):
                answer_data['images'].append(answer.attachment)

            for att in answer.attachments.all():
                if self._is_image_file(att.file.name):
                    answer_data['images'].append(att.file)

            answers_by_section[section_name].append(answer_data)

        return answers_by_section

    def _is_image_file(self, filename):
        """Check if file is an image based on extension"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        return any(filename.lower().endswith(ext) for ext in image_extensions)

    def generate_pdf(self):
        """Generate PDF for this report"""
        from .utils import ReportPDFGenerator
        from django.conf import settings
        import os

        # Ensure the PDF directory exists
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'report_pdfs')
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir, exist_ok=True)

        generator = ReportPDFGenerator(self)
        pdf_path = generator.generate()

        if pdf_path:
            # Update the model with the generated PDF
            from django.core.files import File

            with open(pdf_path, 'rb') as pdf_file:
                self.pdf_file.save(
                    f"{self.document_number}.pdf",
                    File(pdf_file),
                    save=False
                )

            self.pdf_generated_at = timezone.now()
            self.pdf_needs_regeneration = False
            self.save(update_fields=['pdf_file', 'pdf_generated_at', 'pdf_needs_regeneration'])

            # Clean up temporary file
            try:
                os.remove(pdf_path)
            except OSError:
                pass

            return True
        return False

    def get_or_generate_pdf(self):
        """Get existing PDF or generate new one if needed"""
        if not self.pdf_file or self.pdf_needs_regeneration:
            self.generate_pdf()
        return self.pdf_file

    def get_flagged_statistics(self):
        """Calculate statistics for flagged items in this report"""
        flagged_count = 0
        action_count = 0

        for answer in self.answers.all():
            # Check if any selected options are flagged
            if answer.selected_options.filter(is_flag=True).exists():
                flagged_count += 1

            # Check if text answer contains failure/warning keywords
            if answer.text_answer:
                text_lower = answer.text_answer.lower()
                if any(keyword in text_lower for keyword in ['fail', 'incorrect', 'needs attention', 'needs descaling', 'unapproved', 'issue']):
                    flagged_count += 1

        return {
            'flagged_count': flagged_count,
            'action_count': action_count  # Can be enhanced later to track action items
        }

    def get_flagged_answers(self):
        """Get all answers that are flagged or contain issues"""
        flagged_answers = []

        for answer in self.answers.select_related('question', 'question__section').prefetch_related('selected_options').order_by('question__section__order', 'question__order'):
            is_flagged = False
            flag_reason = None
            badge_type = 'default'

            # Check if any selected options are flagged
            flagged_options = answer.selected_options.filter(is_flag=True)
            additional_instructions = None
            if flagged_options.exists():
                is_flagged = True
                flag_reason = ', '.join([opt.text for opt in flagged_options])
                # Get badge_type from the first flagged option
                first_flagged = flagged_options.first()
                if hasattr(first_flagged, 'badge_type') and first_flagged.badge_type != 'default':
                    badge_type = first_flagged.badge_type
                # Collect additional_instructions from all flagged options
                instructions_list = [opt.additional_instructions for opt in flagged_options if opt.additional_instructions]
                if instructions_list:
                    additional_instructions = '\n\n'.join(instructions_list)

            # Check text answer for failure/warning keywords
            if answer.text_answer:
                text_lower = answer.text_answer.lower()
                if 'fail' in text_lower:
                    is_flagged = True
                    flag_reason = answer.text_answer
                    badge_type = 'fail'
                elif any(keyword in text_lower for keyword in ['incorrect', 'needs attention', 'needs descaling', 'unapproved', 'issue', 'dirty']):
                    is_flagged = True
                    flag_reason = answer.text_answer
                    badge_type = 'warning'

            if is_flagged:
                flagged_answers.append({
                    'answer': answer,
                    'question': answer.question,
                    'section': answer.question.section.name if answer.question.section else 'General',
                    'flag_reason': flag_reason,
                    'display_value': answer.get_display_value(),
                    'badge_type': badge_type,
                    'additional_instructions': additional_instructions
                })

        return flagged_answers


class Answer(MyBaseModel):
    """User's response to a specific question"""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    
    # Different answer types
    text_answer = models.TextField(blank=True, null=True)
    selected_options = models.ManyToManyField(QuestionOption, blank=True, related_name='answers')
    file_answer = models.FileField(upload_to='report_answers/', blank=True, null=True)
    signature_answer = models.FileField(upload_to='report_signatures/', blank=True, null=True)
    date_answer = models.DateField(blank=True, null=True)
    number_answer = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Additional fields for notes and attachments
    notes = models.TextField(blank=True, null=True, help_text="Additional notes or comments for this answer")
    attachment = models.FileField(upload_to='answer_attachments/', blank=True, null=True, help_text="Optional file attachment (photo, document, etc.)")
    
    class Meta:
        unique_together = ['report', 'question']
    
    def __str__(self):
        return f"{self.report.document_number} - {self.question.question_text[:30]}..."

    def save(self, *args, **kwargs):
        # Mark the report's PDF for regeneration when an answer changes
        if self.pk:
            # This is an update
            self.report.pdf_needs_regeneration = True
            self.report.save(update_fields=['pdf_needs_regeneration'])

        super().save(*args, **kwargs)

        # If this is a new answer, also mark for regeneration
        if not self.pk or 'force_insert' in kwargs:
            self.report.pdf_needs_regeneration = True
            self.report.save(update_fields=['pdf_needs_regeneration'])
    
    def get_display_value(self):
        """Get the display value for this answer"""
        if self.text_answer:
            return self.text_answer
        elif self.selected_options.exists():
            return ", ".join([opt.text for opt in self.selected_options.all()])
        elif self.file_answer:
            return f"File: {self.file_answer.name}"
        elif self.signature_answer:
            return "Digital Signature"
        elif self.date_answer:
            return self.date_answer.strftime("%Y-%m-%d")
        elif self.number_answer:
            return str(self.number_answer)
        else:
            return "No answer"


class AnswerAttachment(MyBaseModel):
    """An attachment (photo/file) linked to an answer. Supports multiple per answer."""
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='answer_attachments/')
    caption = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Attachment for {self.answer} - {self.file.name}"


class ReportTypeCustomer(MyBaseModel):
    """Links report types to specific customers who can access them"""
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='customer_assignments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='report_type_assignments')
    is_active = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_assignments_made')
    assigned_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this assignment")
    
    class Meta:
        unique_together = ['report_type', 'customer']
        ordering = ['report_type__name', 'customer__businessName']
    
    def __str__(self):
        return f"{self.report_type.name} -> {self.customer.businessName}"


class ReportTypeDistributor(MyBaseModel):
    """Links report types to specific distributors who can access them"""
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='distributor_assignments')
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE, related_name='report_type_assignments')
    is_active = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='distributor_report_assignments_made')
    assigned_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this assignment")

    class Meta:
        unique_together = ['report_type', 'distributor']
        ordering = ['report_type__name', 'distributor__businessname']

    def __str__(self):
        return f"{self.report_type.name} -> {self.distributor.businessname}"


class QuestionTemplate(MyBaseModel):
    """Reusable question templates for common scenarios"""
    name = models.CharField(max_length=255, help_text="Template name (e.g., 'Standard Temperature Check')")
    category = models.CharField(max_length=100, choices=[
        ('temperature', 'Temperature Monitoring'),
        ('cleanliness', 'Cleanliness & Sanitation'),
        ('equipment', 'Equipment Check'),
        ('safety', 'Safety Compliance'),
        ('documentation', 'Documentation'),
        ('general', 'General Inspection'),
        ('custom', 'Custom')
    ], default='general')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    help_text = models.TextField(blank=True, null=True)
    is_required_default = models.BooleanField(default=False, help_text="Default required status when using template")
    
    # Template options (for select/radio/checkbox questions)
    template_options = models.JSONField(default=list, blank=True, help_text="Default options as JSON array")
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_templates')
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"
    
    def increment_usage(self):
        """Increment usage counter when template is used"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class ConditionalRule(MyBaseModel):
    """Advanced conditional logic for complex form flows"""
    name = models.CharField(max_length=255)
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='conditional_rules')
    is_active = models.BooleanField(default=True)
    
    # Condition
    trigger_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='conditional_triggers')
    trigger_value = models.CharField(max_length=255, help_text="Value that triggers this rule")
    trigger_operator = models.CharField(max_length=20, choices=[
        ('equals', 'Equals'),
        ('not_equals', 'Does Not Equal'),
        ('contains', 'Contains'),
        ('not_contains', 'Does Not Contain'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('is_empty', 'Is Empty'),
        ('is_not_empty', 'Is Not Empty')
    ], default='equals')
    
    # Action
    target_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='conditional_targets')
    action = models.CharField(max_length=20, choices=[
        ('show', 'Show Question'),
        ('hide', 'Hide Question'),
        ('require', 'Make Required'),
        ('unrequire', 'Make Optional'),
        ('skip_to', 'Skip To Question')
    ])
    
    # Additional settings
    order = models.PositiveIntegerField(default=0, help_text="Order in which rules are applied")
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.trigger_question.question_text[:30]}..."
    
    def evaluate(self, answer_value):
        """Evaluate if this rule should be triggered based on the answer value"""
        if self.trigger_operator == 'equals':
            return str(answer_value) == str(self.trigger_value)
        elif self.trigger_operator == 'not_equals':
            return str(answer_value) != str(self.trigger_value)
        elif self.trigger_operator == 'contains':
            return str(self.trigger_value).lower() in str(answer_value).lower()
        elif self.trigger_operator == 'not_contains':
            return str(self.trigger_value).lower() not in str(answer_value).lower()
        elif self.trigger_operator == 'is_empty':
            return not answer_value or str(answer_value).strip() == ''
        elif self.trigger_operator == 'is_not_empty':
            return answer_value and str(answer_value).strip() != ''
        elif self.trigger_operator == 'greater_than':
            try:
                return float(answer_value) > float(self.trigger_value)
            except (ValueError, TypeError):
                return False
        elif self.trigger_operator == 'less_than':
            try:
                return float(answer_value) < float(self.trigger_value)
            except (ValueError, TypeError):
                return False
        return False


class ComplianceManager(MyBaseModel):
    """Store compliance managers associated with customers"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='compliance_managers')
    name = models.CharField(max_length=255, help_text="Full name of the compliance manager")
    phone_number = models.CharField(max_length=50, blank=True, null=True, help_text="Contact phone number")

    class Meta:
        ordering = ['name']
        verbose_name = 'Compliance Manager'
        verbose_name_plural = 'Compliance Managers'

    def __str__(self):
        return f"{self.name} ({self.customer.businessName})"
