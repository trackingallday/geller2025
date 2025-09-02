from rest_framework import serializers
from django.contrib.auth.models import User
from chemsapp.models import Customer, Distributor
from .models import (
    ReportType, ReportSection, Question, QuestionOption, 
    Report, Answer, QUESTION_TYPES
)


class UserSerializer(serializers.ModelSerializer):
    """Basic user info for reports"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class CustomerSerializer(serializers.ModelSerializer):
    """Customer info for reports"""
    
    class Meta:
        model = Customer
        fields = ['id', 'businessName', 'address', 'phoneNumber']


class DistributorSerializer(serializers.ModelSerializer):
    """Distributor info for reports"""
    
    class Meta:
        model = Distributor
        fields = ['id', 'businessName', 'address', 'phoneNumber']


class QuestionOptionSerializer(serializers.ModelSerializer):
    """Serializer for question options"""
    
    class Meta:
        model = QuestionOption
        fields = [
            'id', 'text', 'value', 'is_flag', 'additional_instructions', 
            'attached_pdf', 'order'
        ]


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions with their options"""
    options = QuestionOptionSerializer(many=True, read_only=True)
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    parent_question_text = serializers.CharField(source='parent_question.question_text', read_only=True)
    show_when_values = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 'question_type_display',
            'help_text', 'is_required', 'order', 'parent_question',
            'parent_question_text', 'show_when_values', 'options'
        ]
    
    def get_show_when_values(self, obj):
        """Get the list of values that trigger this question to show"""
        return obj.get_show_when_values()


class ReportSectionSerializer(serializers.ModelSerializer):
    """Serializer for report sections with their questions"""
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ReportSection
        fields = ['id', 'name', 'description', 'order', 'questions']


class ReportTypeSerializer(serializers.ModelSerializer):
    """Serializer for report type structure"""
    sections = ReportSectionSerializer(many=True, read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ReportType
        fields = [
            'id', 'name', 'description', 'auto_number_prefix', 'is_active',
            'created_by', 'created_at', 'sections', 'questions'
        ]


class AnswerSerializer(serializers.ModelSerializer):
    """Serializer for question answers"""
    question = QuestionSerializer(read_only=True)
    question_id = serializers.IntegerField(write_only=True)
    selected_options = QuestionOptionSerializer(many=True, read_only=True)
    selected_option_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    display_value = serializers.CharField(source='get_display_value', read_only=True)
    
    class Meta:
        model = Answer
        fields = [
            'id', 'question', 'question_id', 'text_answer', 'number_answer',
            'date_answer', 'file_answer', 'signature_answer', 
            'selected_options', 'selected_option_ids', 'display_value',
            'notes', 'attachment'
        ]
    
    def create(self, validated_data):
        """Create answer with selected options"""
        selected_option_ids = validated_data.pop('selected_option_ids', [])
        answer = Answer.objects.create(**validated_data)
        
        if selected_option_ids:
            options = QuestionOption.objects.filter(id__in=selected_option_ids)
            answer.selected_options.set(options)
        
        return answer
    
    def update(self, instance, validated_data):
        """Update answer with selected options"""
        selected_option_ids = validated_data.pop('selected_option_ids', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update selected options if provided
        if selected_option_ids is not None:
            if selected_option_ids:
                options = QuestionOption.objects.filter(id__in=selected_option_ids)
                instance.selected_options.set(options)
            else:
                instance.selected_options.clear()
        
        return instance


class ReportSerializer(serializers.ModelSerializer):
    """Full report serializer with all data"""
    report_type = ReportTypeSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    distributor = DistributorSerializer(read_only=True)
    prepared_by = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'document_number', 'report_type', 'customer', 'distributor',
            'store_compliance_manager', 'inspection_date', 'prepared_by',
            'status', 'status_display', 'submitted_at', 'reviewed_by', 
            'reviewed_at', 'created_at', 'updated_at', 'answers'
        ]


class ReportSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for submitting complete report with answers"""
    answers = AnswerSerializer(many=True, write_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'customer', 'distributor', 'store_compliance_manager',
            'inspection_date', 'answers'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """Create report with all answers"""
        answers_data = validated_data.pop('answers', [])
        
        # Create the report
        report = Report.objects.create(**validated_data)
        
        # Create answers
        for answer_data in answers_data:
            answer_serializer = AnswerSerializer(data=answer_data)
            if answer_serializer.is_valid():
                answer_serializer.save(report=report)
        
        return report
    
    def update(self, instance, validated_data):
        """Update report and all answers"""
        answers_data = validated_data.pop('answers', [])
        
        # Update report fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Clear existing answers and create new ones
        instance.answers.all().delete()
        
        for answer_data in answers_data:
            answer_serializer = AnswerSerializer(data=answer_data)
            if answer_serializer.is_valid():
                answer_serializer.save(report=instance)
        
        return instance