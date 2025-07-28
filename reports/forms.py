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


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'section', 'help_text', 'is_required', 'order', 'parent_question', 'show_when_parent_value']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter your question here...'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'help_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional help text...'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'parent_question': forms.Select(attrs={'class': 'form-select'}),
            'show_when_parent_value': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('', '-- Select when to show --'),
                ('yes', 'Yes'),
                ('no', 'No')
            ]),
        }
    
    def __init__(self, *args, report_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        if report_type:
            self.fields['section'].queryset = report_type.sections.all()
            # Only allow yes/no questions as parent questions for conditional logic
            self.fields['parent_question'].queryset = report_type.questions.filter(question_type='yesno')
        else:
            self.fields['section'].queryset = ReportSection.objects.none()
            self.fields['parent_question'].queryset = Question.objects.none()
        
        # Update help text to clarify parent question restriction
        self.fields['parent_question'].help_text = "Only Yes/No questions can be used as parent questions"
        self.fields['show_when_parent_value'].help_text = "Select when this question should appear based on the parent question's value"
    
    def clean(self):
        cleaned_data = super().clean()
        parent_question = cleaned_data.get('parent_question')
        show_when_parent_value = cleaned_data.get('show_when_parent_value')
        
        # If parent question is set, validate the trigger value
        if parent_question and show_when_parent_value:
            if show_when_parent_value.lower() not in ['yes', 'no']:
                self.add_error('show_when_parent_value', 
                             "Parent value must be 'yes' or 'no' for Yes/No questions")
        
        # If parent question is set, show_when_parent_value is required
        if parent_question and not show_when_parent_value:
            self.add_error('show_when_parent_value', 
                         "This field is required when a parent question is selected")
        
        return cleaned_data


class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = ['text', 'value', 'is_flag', 'additional_instructions', 'attached_pdf', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PASS / FAIL / N/A'}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'pass / fail / na'}),
            'is_flag': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
        fields = ['text_answer', 'number_answer', 'date_answer', 'file_answer', 'signature_answer']
        widgets = {
            'text_answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'number_answer': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_answer': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'file_answer': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'signature_answer': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }