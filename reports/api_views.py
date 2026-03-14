from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from postmarker.core import PostmarkClient

from .models import Report, ReportType, Answer, QuestionOption, ReportStatus
from .serializers import (
    ReportSerializer, ReportListSerializer, ReportSubmissionSerializer,
    ReportTypeSerializer, CustomerSerializer, DistributorSerializer
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
    Uses lightweight serializer with only report type name instead of full nested object.

    GET /reports/api/reports/
    """
    serializer_class = ReportListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Report.objects.select_related(
            'report_type', 'customer', 'distributor', 'prepared_by'
        ).order_by('-created_at')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reports_by_customer(request, customer_id):
    """
    List all reports for a given customer.

    GET /reports/api/customer/{customer_id}/
    """
    from chemsapp.models import Customer

    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

    reports = Report.objects.filter(customer=customer).select_related(
        'report_type', 'customer', 'distributor', 'prepared_by'
    ).order_by('-created_at')

    serializer = ReportListSerializer(reports, many=True)
    return Response(serializer.data)


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
        "compliance_manager": 5,  // Optional: ID of ComplianceManager
        "store_compliance_manager": "John Doe",  // Optional: Manual entry (fallback if compliance_manager not set)
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
                # Save the report with status set to submitted
                report = serializer.save(
                    report_type=report_type,
                    prepared_by=request.user,
                    status=ReportStatus.SUBMITTED,
                    submitted_at=timezone.now()
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
        "compliance_manager": 5,  // Optional: ID of ComplianceManager
        "store_compliance_manager": "John Doe Updated",  // Optional: Manual entry (fallback if compliance_manager not set)
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
    if report.status == ReportStatus.SUBMITTED and request.user != report.prepared_by:
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
    
    if report.status != ReportStatus.DRAFT:
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
        report.status = ReportStatus.SUBMITTED
        report.submitted_at = timezone.now()
        report.save()

        # Log all images in this report to console
        report.log_all_images()

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
def get_user_profile_api(request):
    """
    API endpoint to get the current user's profile information.

    IMPORTANT: This endpoint is only available for distributors and admins.
    Customer users will receive a 403 Forbidden error.

    GET /reports/api/user/profile/

    For Distributor users, returns:
    {
        "success": true,
        "user_id": 123,
        "profileType": "distributor",
        "distributor_id": 456,
        "distributor_data": { ... },
        "customers": [ ... ]
    }

    For Admin users, returns:
    {
        "success": true,
        "user_id": 123,
        "profileType": "admin",
        "admin_data": { ... },
        "distributors": [ ... ],
        "customers": [ ... ]
    }
    """
    try:
        user = request.user

        from chemsapp.models import Customer, Distributor

        # First check if user belongs to a distributor (via ManyToMany relationship)
        if user.distributors.exists():
            # Handle distributor user
            distributor = user.distributors.first()

            # Get all customers associated with this distributor
            customers = Customer.objects.filter(distributors=distributor)

            return Response(
                {
                    'success': True,
                    'user_id': user.id,
                    'profileType': 'distributor',
                    'distributor_id': distributor.id,
                    'distributor_data': DistributorSerializer(distributor).data,
                    'customers': CustomerSerializer(customers, many=True).data
                },
                status=status.HTTP_200_OK
            )

        # Check if user has a profile
        if not hasattr(user, 'profile'):
            return Response(
                {
                    'success': False,
                    'error': 'User has no profile'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        profile = user.profile
        profile_type = profile.profileType

        if profile_type == 'customer':
            # Customers are not allowed to access this endpoint
            return Response(
                {
                    'success': False,
                    'error': 'This endpoint is only available for distributors and admins'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        elif profile_type == 'admin':
            # Handle admin profile - return basic info plus all distributors and customers
            distributors = Distributor.objects.all()
            customers = Customer.objects.all()

            return Response(
                {
                    'success': True,
                    'user_id': user.id,
                    'profileType': profile_type,
                    'admin_data': {
                        'businessName': profile.businessName,
                        'email': user.email,
                        'username': user.username
                    },
                    'distributors': DistributorSerializer(distributors, many=True).data,
                    'customers': CustomerSerializer(customers, many=True).data
                },
                status=status.HTTP_200_OK
            )

        else:
            return Response(
                {
                    'success': False,
                    'error': f'Unknown profile type: {profile_type}'
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


def send_report_email(report, recipient_email, pdf_content):
    """
    Send a report PDF via email using Postmark.

    Args:
        report: Report instance
        recipient_email: Email address to send to
        pdf_content: Binary PDF content

    Returns:
        True if successful, False otherwise

    Raises:
        Exception: If email sending fails
    """
    postmark = PostmarkClient(server_token=settings.POSTMARK_SERVER_API_TOKEN)

    # Create email with attachment
    email = postmark.emails.Email(
        From='noreply@geller.co.nz',
        To=recipient_email,
        Subject=f'Report {report.document_number} - {report.report_type.name}',
        HtmlBody=f'''
            <html>
            <body>
                <h2>Your Report is Ready</h2>
                <p>Please find attached your report:</p>
                <ul>
                    <li><strong>Report Number:</strong> {report.document_number}</li>
                    <li><strong>Report Type:</strong> {report.report_type.name}</li>
                    <li><strong>Inspection Date:</strong> {report.inspection_date}</li>
                    <li><strong>Status:</strong> {report.get_status_display()}</li>
                </ul>
                <p>Thank you for using Geller Chemical Data Sheets.</p>
            </body>
            </html>
        ''',
        TextBody=f'''
Your Report is Ready

Please find attached your report:

Report Number: {report.document_number}
Report Type: {report.report_type.name}
Inspection Date: {report.inspection_date}
Status: {report.get_status_display()}

Thank you for using Geller Chemical Data Sheets.
        '''
    )

    # Attach the PDF
    email.attach_binary(
        content=pdf_content,
        filename=f'{report.document_number}.pdf'
    )

    # Send the email
    email.send()
    return True


def get_or_generate_report_pdf(report):
    """
    Get existing PDF or generate new one if needed.

    Args:
        report: Report instance

    Returns:
        Binary PDF content

    Raises:
        ValueError: If PDF generation fails
    """
    pdf_file = report.get_or_generate_pdf()

    if not pdf_file:
        raise ValueError('Failed to generate PDF')

    pdf_file.open('rb')
    pdf_content = pdf_file.read()
    pdf_file.close()

    return pdf_content


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def email_report_pdf(request):
    """
    API endpoint to generate and email a report PDF.

    POST /reports/api/email-report-pdf/

    Expected JSON:
    {
        "email_address": "user@example.com",
        "report_id": 123
    }

    Returns:
    {
        "success": true,
        "message": "Report PDF sent to user@example.com",
        "report": {
            "document_number": "REP-0001",
            "report_type": "Monthly Inspection",
            "inspection_date": "2025-01-25",
            "status": "Submitted"
        }
    }
    """
    # Validate request data
    email_address = request.data.get('email_address')
    report_id = request.data.get('report_id')

    if not email_address:
        return Response(
            {
                'success': False,
                'error': 'email_address is required'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if not report_id:
        return Response(
            {
                'success': False,
                'error': 'report_id is required'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get the report
    report = get_object_or_404(Report, pk=report_id)

    try:
        # Generate PDF if needed
        pdf_content = get_or_generate_report_pdf(report)

        # Send email
        send_report_email(report, email_address, pdf_content)

        return Response(
            {
                'success': True,
                'message': f'Report PDF sent to {email_address}',
                'report': {
                    'document_number': report.document_number,
                    'report_type': report.report_type.name,
                    'inspection_date': report.inspection_date,
                    'status': report.get_status_display()
                }
            },
            status=status.HTTP_200_OK
        )

    except ValueError as e:
        return Response(
            {
                'success': False,
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': f'Failed to send email: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )