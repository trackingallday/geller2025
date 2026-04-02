from rest_framework import serializers
from django.contrib.auth.models import User
from chemsapp.models import Customer, Distributor, CustomerContact
from .models import (
    ReportType, ReportSection, Question, QuestionOption,
    Report, Answer, AnswerAttachment, ComplianceManager, QUESTION_TYPES
)
import base64
import io
import uuid
import os
from django.core.files.base import ContentFile
from django.conf import settings


class Base64FileField(serializers.FileField):
    """Custom file field that can handle base64 data or regular file uploads"""

    def to_internal_value(self, data):
        # If it's a string starting with 'data:', it's base64
        if isinstance(data, str) and data.startswith('data:'):
            try:
                # Parse base64 data
                format_part, imgstr = data.split(';base64,')
                ext = format_part.split('/')[-1]

                # Generate unique filename
                filename = f'mobile_photo_{uuid.uuid4().hex[:8]}.{ext}'

                # Ensure the upload directory exists
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'answer_attachments')
                os.makedirs(upload_dir, exist_ok=True)

                print(f"Ensured upload directory exists: {upload_dir}")

                # Convert base64 to file
                file_data = ContentFile(base64.b64decode(imgstr), name=filename)

                print(f"Created ContentFile: {filename}, size: {len(imgstr)} chars")
                return file_data

            except Exception as e:
                print(f"Error processing base64 data: {e}")
                raise serializers.ValidationError(f"Invalid base64 file data: {e}")

        # Otherwise, use default file field handling
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    """Basic user info for reports"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ComplianceManagerSerializer(serializers.ModelSerializer):
    """Serializer for compliance managers"""

    class Meta:
        model = ComplianceManager
        fields = ['id', 'name', 'phone_number']


class CustomerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerContact
        fields = ('id', 'name', 'role', 'email', 'phone', 'receive_report')


class CustomerSerializer(serializers.ModelSerializer):
    """Customer info for reports"""
    compliance_managers = ComplianceManagerSerializer(many=True, read_only=True)
    contacts = CustomerContactSerializer(many=True, read_only=True)
    email = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'businessName', 'address', 'phoneNumber', 'compliance_managers', 'contacts', 'email']

    def get_email(self, obj):
        return obj.user.email if obj.user else None


class DistributorSerializer(serializers.ModelSerializer):
    """Distributor info for reports"""

    class Meta:
        model = Distributor
        fields = ['id', 'businessname', 'address', 'phonenumber']


class QuestionOptionSerializer(serializers.ModelSerializer):
    """Serializer for question options"""
    badge_type_display = serializers.CharField(source='get_badge_type_display', read_only=True)

    class Meta:
        model = QuestionOption
        fields = [
            'id', 'text', 'value', 'is_flag', 'badge_type', 'badge_type_display',
            'additional_instructions', 'attached_pdf', 'order'
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
    assigned_customers = serializers.SerializerMethodField()
    assigned_distributors = serializers.SerializerMethodField()

    class Meta:
        model = ReportType
        fields = [
            'id', 'name', 'description', 'auto_number_prefix', 'is_active',
            'created_by', 'created_at', 'sections', 'questions',
            'assigned_customers', 'assigned_distributors'
        ]

    def get_assigned_customers(self, obj):
        """Get all customers assigned to this report type"""
        customers = obj.get_assigned_customers()
        return CustomerSerializer(customers, many=True).data

    def get_assigned_distributors(self, obj):
        """Get all distributors assigned to this report type"""
        distributors = obj.get_assigned_distributors()
        return DistributorSerializer(distributors, many=True).data


class AnswerAttachmentSerializer(serializers.ModelSerializer):
    file = Base64FileField()

    class Meta:
        model = AnswerAttachment
        fields = ['id', 'file', 'caption']


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
    attachment = Base64FileField(required=False, allow_null=True)
    attachments = AnswerAttachmentSerializer(many=True, read_only=True)
    attachments_data = serializers.ListField(
        child=Base64FileField(),
        write_only=True,
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Answer
        fields = [
            'id', 'question', 'question_id', 'text_answer', 'number_answer',
            'date_answer', 'file_answer', 'signature_answer',
            'selected_options', 'selected_option_ids', 'display_value',
            'notes', 'attachment', 'attachments', 'attachments_data'
        ]

    def create(self, validated_data):
        """Create answer with selected options and attachments"""
        selected_option_ids = validated_data.pop('selected_option_ids', [])
        attachments_data = validated_data.pop('attachments_data', [])
        legacy_attachment = validated_data.pop('attachment', None)

        answer = Answer.objects.create(**validated_data)

        if selected_option_ids:
            options = QuestionOption.objects.filter(id__in=selected_option_ids)
            answer.selected_options.set(options)

        for file_data in attachments_data:
            AnswerAttachment.objects.create(answer=answer, file=file_data)

        if legacy_attachment:
            AnswerAttachment.objects.create(answer=answer, file=legacy_attachment)

        return answer

    def update(self, instance, validated_data):
        """Update answer with selected options and attachments"""
        selected_option_ids = validated_data.pop('selected_option_ids', None)
        attachments_data = validated_data.pop('attachments_data', None)
        legacy_attachment = validated_data.pop('attachment', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if selected_option_ids is not None:
            if selected_option_ids:
                options = QuestionOption.objects.filter(id__in=selected_option_ids)
                instance.selected_options.set(options)
            else:
                instance.selected_options.clear()

        if attachments_data is not None:
            instance.attachments.all().delete()
            for file_data in attachments_data:
                AnswerAttachment.objects.create(answer=instance, file=file_data)

        if legacy_attachment:
            AnswerAttachment.objects.create(answer=instance, file=legacy_attachment)

        return instance


class ReportListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for report list view"""
    report_type_name = serializers.CharField(source='report_type.name', read_only=True)
    customer_name = serializers.CharField(source='customer.businessName', read_only=True)
    distributor_name = serializers.CharField(source='distributor.businessname', read_only=True)
    compliance_manager_name = serializers.CharField(read_only=True)
    prepared_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'document_number', 'report_type_name', 'customer_name', 'distributor_name',
            'compliance_manager', 'store_compliance_manager', 'compliance_manager_name',
            'inspection_date', 'prepared_by_name',
            'status', 'status_display', 'submitted_at',
            'created_at', 'updated_at',
            'pdf_file', 'pdf_generated_at', 'pdf_needs_regeneration'
        ]

    def get_prepared_by_name(self, obj):
        """Get full name or username of preparer"""
        if obj.prepared_by:
            if obj.prepared_by.first_name and obj.prepared_by.last_name:
                return f"{obj.prepared_by.first_name} {obj.prepared_by.last_name}"
            return obj.prepared_by.username
        return None


class ReportSerializer(serializers.ModelSerializer):
    """Full report serializer with all data"""
    report_type = ReportTypeSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    distributor = DistributorSerializer(read_only=True)
    compliance_manager_obj = ComplianceManagerSerializer(source='compliance_manager', read_only=True)
    compliance_manager_name = serializers.CharField(read_only=True)
    prepared_by = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'document_number', 'report_type', 'customer', 'distributor',
            'compliance_manager', 'compliance_manager_obj', 'store_compliance_manager',
            'compliance_manager_name', 'inspection_date', 'prepared_by',
            'status', 'status_display', 'submitted_at', 'reviewed_by',
            'reviewed_at', 'created_at', 'updated_at', 'answers',
            'pdf_file', 'pdf_generated_at', 'pdf_needs_regeneration'
        ]


class ReportSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for submitting complete report with answers"""
    answers = AnswerSerializer(many=True, write_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'customer', 'distributor', 'compliance_manager',
            'store_compliance_manager', 'inspection_date', 'answers'
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