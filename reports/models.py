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
