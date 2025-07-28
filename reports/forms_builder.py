from django import forms
from django.forms import inlineformset_factory, modelformset_factory
from .models import (
    ReportType, ReportSection, Question, QuestionOption, QuestionTemplate,
    ReportTypeCustomer, ConditionalRule, QUESTION_TYPES
)
from chemsapp.models import Customer


class EnhancedReportTypeForm(forms.ModelForm):
    """Enhanced form for creating report types with additional features"""
    
    class Meta:
        model = ReportType
        fields = ['name', 'description', 'auto_number_prefix', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Monthly Store Audit Report',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Describe the purpose and scope of this report type...'
            }),
            'auto_number_prefix': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., MSA (creates MSA0001, MSA0002...)', 
                'maxlength': 10
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text and improved labels
        self.fields['name'].help_text = "Clear, descriptive name for this report type"
        self.fields['auto_number_prefix'].help_text = "Short prefix for auto-generated document numbers (optional)"
        self.fields['is_active'].help_text = "Only active report types can be used to create new reports"


class QuickSectionForm(forms.ModelForm):
    """Quick form for creating sections in the builder"""
    
    class Meta:
        model = ReportSection
        fields = ['name', 'description', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Section name (e.g., Equipment Check)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Optional description...'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0,
                'value': 0
            })
        }


class QuickQuestionForm(forms.ModelForm):
    """Quick form for creating questions in the builder"""
    
    class Meta:
        model = Question
        fields = [
            'question_text', 'question_type', 'section', 'help_text', 
            'is_required', 'order', 'parent_question', 'show_when_parent_value'
        ]
        widgets = {
            'question_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Enter your question here...'
            }),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'help_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Additional help or instructions...'
            }),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'parent_question': forms.Select(attrs={'class': 'form-select'}),
            'show_when_parent_value': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Value that shows this question'
            }),
        }
    
    def __init__(self, *args, report_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        if report_type:
            self.fields['section'].queryset = report_type.sections.all()
            self.fields['section'].empty_label = "No section (general)"
            self.fields['parent_question'].queryset = report_type.questions.all()
            self.fields['parent_question'].empty_label = "No parent question"
        else:
            self.fields['section'].queryset = ReportSection.objects.none()
            self.fields['parent_question'].queryset = Question.objects.none()


class QuestionTemplateForm(forms.ModelForm):
    """Form for creating and editing question templates"""
    
    # Dynamic field for adding template options
    template_options_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter options one per line (for choice questions):\nPass\nFail\nN/A'
        }),
        required=False,
        help_text="For select/radio/checkbox questions, enter each option on a new line"
    )
    
    class Meta:
        model = QuestionTemplate
        fields = [
            'name', 'category', 'question_text', 'question_type', 
            'help_text', 'is_required_default', 'template_options_text'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Standard Temperature Check'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'question_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Enter the template question text...'
            }),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'help_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Help text for this question...'
            }),
            'is_required_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*kwargs)
        # Pre-populate template options text if editing
        if self.instance.pk and self.instance.template_options:
            options_text = '\n'.join([
                opt['text'] if isinstance(opt, dict) else str(opt) 
                for opt in self.instance.template_options
            ])
            self.initial['template_options_text'] = options_text
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Process template options text
        options_text = self.cleaned_data.get('template_options_text', '').strip()
        if options_text and instance.question_type in ['select', 'radio', 'checkbox']:
            options = []
            for line in options_text.split('\n'):
                line = line.strip()
                if line:
                    options.append({
                        'text': line,
                        'value': line.lower().replace(' ', '_'),
                        'is_flag': 'fail' in line.lower() or 'reject' in line.lower()
                    })
            instance.template_options = options
        else:
            instance.template_options = []
        
        if commit:
            instance.save()
        return instance


class CustomerAssignmentForm(forms.Form):
    """Form for assigning customers to report types"""
    
    customers = forms.ModelMultipleChoiceField(
        queryset=Customer.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text="Select which customers can access this report type"
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional notes about these assignments...'
        }),
        required=False
    )
    
    def __init__(self, *args, report_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        if report_type:
            # Pre-select currently assigned customers
            assigned_customers = report_type.get_assigned_customers()
            self.fields['customers'].initial = assigned_customers


class ConditionalRuleForm(forms.ModelForm):
    """Form for creating conditional rules"""
    
    class Meta:
        model = ConditionalRule
        fields = [
            'name', 'trigger_question', 'trigger_operator', 'trigger_value',
            'target_question', 'action', 'is_active', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Show follow-up if failed'
            }),
            'trigger_question': forms.Select(attrs={'class': 'form-select'}),
            'trigger_operator': forms.Select(attrs={'class': 'form-select'}),
            'trigger_value': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Value that triggers this rule'
            }),
            'target_question': forms.Select(attrs={'class': 'form-select'}),
            'action': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
    
    def __init__(self, *args, report_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        if report_type:
            # Limit questions to this report type
            questions = report_type.questions.all().order_by('section__order', 'order')
            self.fields['trigger_question'].queryset = questions
            self.fields['target_question'].queryset = questions
        else:
            self.fields['trigger_question'].queryset = Question.objects.none()
            self.fields['target_question'].queryset = Question.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        trigger_question = cleaned_data.get('trigger_question')
        target_question = cleaned_data.get('target_question')
        
        # Ensure trigger and target questions are different
        if trigger_question and target_question and trigger_question == target_question:
            raise forms.ValidationError("Trigger question and target question cannot be the same.")
        
        return cleaned_data


# Formsets for bulk operations
QuestionOptionFormSet = inlineformset_factory(
    Question, 
    QuestionOption,
    fields=['text', 'value', 'is_flag', 'additional_instructions', 'order'],
    extra=3,
    can_delete=True,
    widgets={
        'text': forms.TextInput(attrs={'class': 'form-control'}),
        'value': forms.TextInput(attrs={'class': 'form-control'}),
        'is_flag': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        'additional_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
    }
)


class BulkQuestionImportForm(forms.Form):
    """Form for importing multiple questions from CSV or text"""
    
    import_format = forms.ChoiceField(
        choices=[
            ('csv', 'CSV File'),
            ('text', 'Text (one question per line)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='text'
    )
    
    csv_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text="CSV with columns: question_text, question_type, section, is_required"
    )
    
    text_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Enter questions, one per line...'
        }),
        required=False,
        help_text="Enter one question per line"
    )
    
    default_question_type = forms.ChoiceField(
        choices=QUESTION_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='text',
        help_text="Default question type for text import"
    )
    
    target_section = forms.ModelChoiceField(
        queryset=ReportSection.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="No section (general)",
        help_text="Section to add imported questions to"
    )
    
    def __init__(self, *args, report_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        if report_type:
            self.fields['target_section'].queryset = report_type.sections.all()
    
    def clean(self):
        cleaned_data = super().clean()
        import_format = cleaned_data.get('import_format')
        csv_file = cleaned_data.get('csv_file')
        text_content = cleaned_data.get('text_content')
        
        if import_format == 'csv' and not csv_file:
            raise forms.ValidationError("Please upload a CSV file.")
        elif import_format == 'text' and not text_content:
            raise forms.ValidationError("Please enter text content.")
        
        return cleaned_data