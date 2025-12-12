from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Report
from chemsapp.models import Customer, Distributor


@login_required
def completed_reports_list(request):
    """
    List all completed reports with filtering by distributor, customer, status, and date range
    """
    # Base queryset - exclude drafts and rejected by default
    reports = Report.objects.select_related(
        'report_type', 'customer', 'distributor', 'prepared_by'
    ).exclude(status__in=['draft', 'rejected']).order_by('-inspection_date', '-created_at')

    # Get filter parameters
    distributor_id = request.GET.get('distributor')
    customer_id = request.GET.get('customer')
    status_filter = request.GET.get('status', 'all')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('search')

    # Apply filters
    if distributor_id:
        reports = reports.filter(distributor_id=distributor_id)

    if customer_id:
        reports = reports.filter(customer_id=customer_id)

    if status_filter and status_filter != 'all':
        reports = reports.filter(status=status_filter)

    if date_from:
        reports = reports.filter(inspection_date__gte=date_from)

    if date_to:
        reports = reports.filter(inspection_date__lte=date_to)

    if search_query:
        reports = reports.filter(
            Q(document_number__icontains=search_query) |
            Q(report_type__name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all distributors and customers for filter dropdowns
    distributors = Distributor.objects.all().order_by('businessName')
    customers = Customer.objects.all().order_by('businessName')

    # Build context with filter preservation
    context = {
        'page_obj': page_obj,
        'title': 'Completed Reports',
        'distributors': distributors,
        'customers': customers,
        'selected_distributor': distributor_id,
        'selected_customer': customer_id,
        'selected_status': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }

    return render(request, 'reports/completed_reports_list.html', context)


@login_required
def completed_report_detail(request, pk):
    """
    View detailed information about a completed report with PDF management options
    """
    report = get_object_or_404(
        Report.objects.select_related('report_type', 'customer', 'distributor', 'prepared_by', 'reviewed_by'),
        pk=pk
    )

    # Get answers organized by section
    answers_by_section = {}
    for answer in report.answers.select_related('question', 'question__section').prefetch_related('selected_options'):
        section_name = answer.question.section.name if answer.question.section else "General"

        if section_name not in answers_by_section:
            answers_by_section[section_name] = []

        answers_by_section[section_name].append({
            'question': answer.question,
            'answer': answer,
            'display_value': answer.get_display_value()
        })

    # Get flagged items statistics
    flagged_stats = report.get_flagged_statistics()
    flagged_answers = report.get_flagged_answers()

    context = {
        'report': report,
        'answers_by_section': answers_by_section,
        'flagged_stats': flagged_stats,
        'flagged_answers': flagged_answers,
        'title': f'Report: {report.document_number}',
        'has_pdf': bool(report.pdf_file),
        'needs_regeneration': report.pdf_needs_regeneration,
    }

    return render(request, 'reports/completed_report_detail.html', context)


@login_required
def generate_pdf_view(request, pk):
    """
    Generate or regenerate PDF for a report
    """
    report = get_object_or_404(Report, pk=pk)

    if request.method == 'POST':
        try:
            success = report.generate_pdf()

            if success:
                messages.success(
                    request,
                    f'PDF generated successfully for report {report.document_number}!'
                )
            else:
                messages.error(
                    request,
                    f'Failed to generate PDF for report {report.document_number}. Please try again.'
                )
        except Exception as e:
            messages.error(
                request,
                f'Error generating PDF: {str(e)}'
            )

        return redirect('reports:completed_report_detail', pk=report.pk)

    # If GET request, show confirmation page
    context = {
        'report': report,
        'title': f'Generate PDF: {report.document_number}'
    }
    return render(request, 'reports/completed_report_generate_pdf.html', context)


@login_required
def view_pdf(request, pk):
    """
    View or download PDF for a report
    Generates PDF if it doesn't exist
    """
    report = get_object_or_404(Report, pk=pk)

    # Get download parameter (if present, force download instead of inline view)
    download = request.GET.get('download', '0') == '1'

    # Generate PDF if it doesn't exist or needs regeneration
    if not report.pdf_file or report.pdf_needs_regeneration:
        try:
            success = report.generate_pdf()
            if not success:
                messages.error(request, 'Failed to generate PDF. Please try again.')
                return redirect('reports:completed_report_detail', pk=report.pk)
        except Exception as e:
            messages.error(request, f'Error generating PDF: {str(e)}')
            return redirect('reports:completed_report_detail', pk=report.pk)

    # Serve the PDF file
    try:
        pdf_file = report.pdf_file
        if not pdf_file:
            raise Http404("PDF file not found")

        response = FileResponse(
            pdf_file.open('rb'),
            content_type='application/pdf'
        )

        # Set filename
        filename = f"{report.document_number}.pdf"

        if download:
            # Force download
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        else:
            # View inline in browser
            response['Content-Disposition'] = f'inline; filename="{filename}"'

        return response

    except Exception as e:
        messages.error(request, f'Error serving PDF: {str(e)}')
        return redirect('reports:completed_report_detail', pk=report.pk)


@login_required
def browse_pdfs(request):
    """
    Browse all generated PDFs with thumbnails and quick access
    """
    # Get all reports with PDFs
    reports = Report.objects.select_related(
        'report_type', 'customer', 'distributor'
    ).exclude(
        pdf_file=''
    ).exclude(
        pdf_file__isnull=True
    ).order_by('-pdf_generated_at')

    # Apply filters
    distributor_id = request.GET.get('distributor')
    customer_id = request.GET.get('customer')

    if distributor_id:
        reports = reports.filter(distributor_id=distributor_id)

    if customer_id:
        reports = reports.filter(customer_id=customer_id)

    # Pagination
    paginator = Paginator(reports, 24)  # Grid layout, so more per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all distributors and customers for filters
    distributors = Distributor.objects.all().order_by('businessName')
    customers = Customer.objects.all().order_by('businessName')

    context = {
        'page_obj': page_obj,
        'title': 'Browse PDFs',
        'distributors': distributors,
        'customers': customers,
        'selected_distributor': distributor_id,
        'selected_customer': customer_id,
    }

    return render(request, 'reports/browse_pdfs.html', context)
