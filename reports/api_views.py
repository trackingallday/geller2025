from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from .models import Report, ReportType, Answer, QuestionOption
from .serializers import (
    ReportSerializer, ReportSubmissionSerializer, 
    ReportTypeSerializer
)


class ReportDetailAPIView(generics.RetrieveAPIView):
    """
    API view to retrieve a complete report with all data in JSON format.
    
    GET /reports/api/reports/{id}/
    """
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        return Report.objects.select_related(
            'report_type', 'customer', 'distributor', 'prepared_by', 'reviewed_by'
        ).prefetch_related(
            'answers__question__options',
            'answers__selected_options',
            'report_type__sections__questions__options'
        )


class ReportListAPIView(generics.ListAPIView):
    """
    API view to list all reports with basic info.
    
    GET /reports/api/reports/
    """
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Report.objects.select_related(
            'report_type', 'customer', 'distributor', 'prepared_by'
        ).order_by('-created_at')


class ReportTypeListAPIView(generics.ListAPIView):
    """
    API view to list all available report types.
    
    GET /reports/api/report-types/
    """
    serializer_class = ReportTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ReportType.objects.filter(is_active=True).prefetch_related(
            'sections__questions__options',
            'questions__options'
        ).order_by('name')


class ReportTypeDetailAPIView(generics.RetrieveAPIView):
    """
    API view to retrieve a report type structure for creating new reports.
    
    GET /reports/api/report-types/{id}/
    """
    serializer_class = ReportTypeSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        return ReportType.objects.prefetch_related(
            'sections__questions__options',
            'questions__options'
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_report_api(request, report_type_id):
    """
    API endpoint to create a new report instance for a specific report type.
    
    POST /reports/api/report-types/{report_type_id}/create/
    
    Expected JSON structure:
    {
        "customer": 1,
        "distributor": 2,
        "store_compliance_manager": "John Doe",
        "inspection_date": "2024-01-15",
        "answers": [
            {
                "question_id": 1,
                "text_answer": "Sample text answer"
            },
            {
                "question_id": 2,
                "selected_option_ids": [5, 6]
            },
            {
                "question_id": 3,
                "number_answer": 25.5
            },
            {
                "question_id": 4,
                "date_answer": "2024-01-15"
            }
        ]
    }
    """
    report_type = get_object_or_404(ReportType, pk=report_type_id, is_active=True)
    
    try:
        with transaction.atomic():
            # Prepare data for report creation
            report_data = request.data.copy()
            report_data['report_type'] = report_type.pk
            report_data['prepared_by'] = request.user.pk
            
            # Create serializer and validate
            serializer = ReportSubmissionSerializer(data=report_data)
            
            if serializer.is_valid():
                # Save the report
                report = serializer.save(
                    report_type=report_type,
                    prepared_by=request.user
                )
                
                # Return the complete report data
                response_serializer = ReportSerializer(report)
                return Response(
                    {
                        'success': True,
                        'message': f'Report "{report.document_number}" created successfully',
                        'report': response_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {
                        'success': False,
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_report_api(request, report_id):
    """
    API endpoint to update an existing report with new answers.
    
    PUT/PATCH /reports/api/reports/{report_id}/update/
    
    Expected JSON structure (same as create_report_api):
    {
        "customer": 1,
        "distributor": 2,
        "store_compliance_manager": "John Doe Updated",
        "inspection_date": "2024-01-16",
        "answers": [
            {
                "question_id": 1,
                "text_answer": "Updated text answer"
            },
            {
                "question_id": 2,
                "selected_option_ids": [7]
            }
        ]
    }
    """
    report = get_object_or_404(Report, pk=report_id)
    
    # Check if user can modify this report
    if report.status == 'submitted' and request.user != report.prepared_by:
        return Response(
            {
                'success': False,
                'error': 'Cannot modify submitted reports unless you are the creator'
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        with transaction.atomic():
            serializer = ReportSubmissionSerializer(
                report, 
                data=request.data, 
                partial=(request.method == 'PATCH')
            )
            
            if serializer.is_valid():
                updated_report = serializer.save()
                
                # Return the updated report data
                response_serializer = ReportSerializer(updated_report)
                return Response(
                    {
                        'success': True,
                        'message': f'Report "{updated_report.document_number}" updated successfully',
                        'report': response_serializer.data
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'success': False,
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_report_api(request, report_id):
    """
    API endpoint to submit a report for review.
    
    POST /reports/api/reports/{report_id}/submit/
    """
    report = get_object_or_404(Report, pk=report_id)
    
    if report.status != 'draft':
        return Response(
            {
                'success': False,
                'error': f'Cannot submit report with status: {report.get_status_display()}'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if report.prepared_by != request.user:
        return Response(
            {
                'success': False,
                'error': 'Only the report creator can submit it'
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        report.status = 'submitted'
        report.submitted_at = timezone.now()
        report.save()
        
        response_serializer = ReportSerializer(report)
        return Response(
            {
                'success': True,
                'message': f'Report "{report.document_number}" submitted successfully',
                'report': response_serializer.data
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_questions_api(request, report_type_id):
    """
    API endpoint to get all questions for a report type (useful for building forms).
    
    GET /reports/api/report-types/{report_type_id}/questions/
    """
    report_type = get_object_or_404(
        ReportType.objects.prefetch_related(
            'sections__questions__options',
            'questions__options'
        ),
        pk=report_type_id,
        is_active=True
    )
    
    serializer = ReportTypeSerializer(report_type)
    
    return Response(
        {
            'success': True,
            'report_type': serializer.data
        },
        status=status.HTTP_200_OK
    )