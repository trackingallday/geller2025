from django import forms
from django.forms import inlineformset_factory
from .models import (
    ReportType, ReportSection, Question, QuestionOption, 
    Report, Answer, QUESTION_TYPES
)
from chemsapp.models import Customer, Distributor


class ReportTypeForm(forms.ModelForm):
    class Meta:
        model = ReportType
        fields = ['name', 'description', 'auto_number_prefix', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Monthly Audit Report - Grocery'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description of this report type...'}),
            'auto_number_prefix': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MAR', 'maxlength': 10}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ReportSectionForm(forms.ModelForm):
    class Meta:
        model = ReportSection
        fields = ['name', 'description', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PRODUCE DEPARTMENT'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Section description...'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class BootstrapCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """Custom checkbox widget with proper Bootstrap styling"""
    
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        # Add Bootstrap classes to each checkbox
        if attrs is None:
            attrs = {}
        attrs.update({'class': 'form-check-input'})
        option['attrs'] = attrs
        return option
    
    class Media:
        css = {
            'all': ('reports/css/custom-checkboxes.css',)
        }


class QuestionForm(forms.ModelForm):
    show_when_parent_values = forms.MultipleChoiceField(
        required=False,
        widget=BootstrapCheckboxSelectMultiple(),
        help_text="Select one or more values that should trigger this question to show"
    )
    
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'section', 'help_text', 'is_required', 'order', 'parent_question', 'show_when_parent_values']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter your question here...'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'help_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional help text...'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'parent_question': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, report_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        if report_type:
            self.fields['section'].queryset = report_type.sections.all()
            # Allow yes/no and multi-choice questions as parent questions for conditional logic
            self.fields['parent_question'].queryset = report_type.questions.filter(
                question_type__in=['yesno', 'select', 'radio', 'checkbox']
            )
        else:
            self.fields['section'].queryset = ReportSection.objects.none()
            self.fields['parent_question'].queryset = Question.objects.none()
        
        # Update help text to clarify parent question restriction
        self.fields['parent_question'].help_text = "Select a Yes/No or multiple choice question to use as parent"
        
        # Set up initial choices for show_when_parent_values
        self._setup_parent_value_choices()
        
        # Load existing values for the multiple choice field
        if self.instance and self.instance.pk:
            existing_values = self.instance.get_show_when_values()
            self.fields['show_when_parent_values'].initial = existing_values
    
    def _setup_parent_value_choices(self):
        """Set up choices for show_when_parent_values based on the parent question"""
        choices = []
        parent_question = None
        
        # Priority order: data from POST > instance parent > initial data
        if hasattr(self, 'data') and self.data.get('parent_question'):
            try:
                parent_question = Question.objects.get(pk=self.data['parent_question'])
            except (Question.DoesNotExist, ValueError):
                pass
        elif self.instance and self.instance.pk and self.instance.parent_question:
            parent_question = self.instance.parent_question
        elif self.initial.get('parent_question'):
            try:
                parent_question = Question.objects.get(pk=self.initial['parent_question'])
            except Question.DoesNotExist:
                pass
        
        if parent_question:
            choices.extend(self._get_question_choices(parent_question))
        else:
            # If no parent question is selected, show a helpful message
            choices = [('', 'Select a parent question first')]
        
        self.fields['show_when_parent_values'].choices = choices
    
    def _get_question_choices(self, question):
        """Get available choices for a given question"""
        if question.question_type == 'yesno':
            return [('yes', 'Yes'), ('no', 'No')]
        elif question.question_type in ['select', 'radio', 'checkbox']:
            return [(option.value, option.text) for option in question.options.all().order_by('order')]
        return []
    
    def clean(self):
        cleaned_data = super().clean()
        parent_question = cleaned_data.get('parent_question')
        show_when_parent_values = cleaned_data.get('show_when_parent_values')
        
        # If parent question is set, validate the trigger values
        if parent_question and show_when_parent_values:
            valid_choices = self._get_question_choices(parent_question)
            valid_values = [choice[0] for choice in valid_choices]
            
            for value in show_when_parent_values:
                if value not in valid_values:
                    question_type_display = parent_question.get_question_type_display()
                    self.add_error('show_when_parent_values', 
                                 f"Invalid value '{value}' for {question_type_display} question. "
                                 f"Valid options: {', '.join(valid_values)}")
        
        # If parent question is set, at least one trigger value is required
        if parent_question and not show_when_parent_values:
            self.add_error('show_when_parent_values', 
                         "Select at least one value when a parent question is selected")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set the show_when_parent_values using our model method
        show_when_parent_values = self.cleaned_data.get('show_when_parent_values', [])
        if show_when_parent_values:
            instance.set_show_when_values(show_when_parent_values)
        
        if commit:
            instance.save()
        return instance


class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = ['text', 'value', 'is_flag', 'badge_type', 'additional_instructions', 'attached_pdf', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PASS / FAIL / N/A'}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'pass / fail / na'}),
            'is_flag': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'badge_type': forms.Select(attrs={'class': 'form-control'}),
            'additional_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Instructions when this option is selected...'}),
            'attached_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['customer', 'distributor', 'store_compliance_manager', 'inspection_date']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'distributor': forms.Select(attrs={'class': 'form-select'}),
            'store_compliance_manager': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Manager name'}),
            'inspection_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, report_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all()
        self.fields['distributor'].queryset = Distributor.objects.all()


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text_answer', 'number_answer', 'date_answer', 'file_answer', 'signature_answer', 'notes', 'attachment']
        widgets = {
            'text_answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'number_answer': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_answer': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'file_answer': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'signature_answer': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add notes or comments for this answer...'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf,.doc,.docx'}),
        }