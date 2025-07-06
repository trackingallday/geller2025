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
    ('client_select', 'Client Select'),
]

REPORT_STATUS = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]


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
    show_when_parent_value = models.CharField(max_length=255, blank=True, null=True, help_text="Show this question when parent has this value")
    
    class Meta:
        ordering = ['order', 'question_text']
    
    def __str__(self):
        return f"{self.report_type.name} - {self.question_text[:50]}..."


class QuestionOption(MyBaseModel):
    """Options for select/radio/checkbox questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    is_flag = models.BooleanField(default=False, help_text="Mark this option as requiring attention")
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
    store_compliance_manager = models.CharField(max_length=255, blank=True, null=True)
    inspection_date = models.DateField(default=timezone.now)
    prepared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_prepared')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='draft')
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='reports_reviewed')
    reviewed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document_number} - {self.report_type.name}"
    
    def save(self, *args, **kwargs):
        if not self.document_number:
            self.document_number = self.report_type.get_next_document_number()
        super().save(*args, **kwargs)


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
    
    class Meta:
        unique_together = ['report', 'question']
    
    def __str__(self):
        return f"{self.report.document_number} - {self.question.question_text[:30]}..."
    
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


class ConditionalRule(MyBaseModel):
    """Advanced conditional logic for complex form flows"""
    name = models.CharField(max_length=255)
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='conditional_rules')
    
    # Condition
    trigger_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='conditional_triggers')
    trigger_value = models.CharField(max_length=255)
    
    # Action
    target_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='conditional_targets')
    action = models.CharField(max_length=20, choices=[
        ('show', 'Show Question'),
        ('hide', 'Hide Question'),
        ('require', 'Make Required'),
        ('unrequire', 'Make Optional')
    ])
    
    def __str__(self):
        return f"{self.name} - {self.trigger_question.question_text[:30]}..."
