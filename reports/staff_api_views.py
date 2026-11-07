"""JSON reads and PDF actions for the admin app's reports screen.

The report admin carries the real work: generating and regenerating PDFs,
and showing the images an answer carries. These endpoints expose the same
things to the admin app, calling the model's own generate_pdf() rather
than repeating what it does.
"""
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date

from chemsapp.staff_api import error, json_body, ok, search_q, staff_api

from .models import Answer, Report, ReportType

PAGE_SIZE = 50


def _file(field):
    if not field:
        return None
    try:
        return {'name': field.name.rsplit('/', 1)[-1], 'url': field.url}
    except ValueError:
        return None


def _when(value):
    return value.isoformat() if value else None


def _subject(report):
    """Who the report is about: a customer, a distributor or a prospect."""
    if report.customer_id:
        return {'kind': 'customer', 'id': report.customer_id,
                'name': report.customer.businessName}
    if report.prospect_id:
        return {'kind': 'prospect', 'id': report.prospect_id,
                'name': report.prospect.business_name}
    if report.distributor_id:
        return {'kind': 'distributor', 'id': report.distributor_id,
                'name': report.distributor.businessname}
    return None


def _row(report):
    return {
        'id': report.pk,
        'document_number': report.document_number,
        'report_type': {
            'id': report.report_type_id,
            'name': report.report_type.name,
        } if report.report_type_id else None,
        'subject': _subject(report),
        'status': report.status,
        'inspection_date': _when(report.inspection_date),
        'prepared_by': report.prepared_by.username if report.prepared_by_id else None,
        'compliance_manager': report.compliance_manager_name or None,
        'pdf': _file(report.pdf_file),
        'pdf_needs_regeneration': report.pdf_needs_regeneration,
        'pdf_generated_at': _when(report.pdf_generated_at),
        'submitted_at': _when(report.submitted_at),
        'created_at': _when(report.created_at),
    }


@staff_api
def report_list(request):
    """Reports, filtered the way the completed-reports page filters them."""
    reports = (
        Report.objects
        .select_related('report_type', 'customer', 'distributor', 'prospect',
                        'prepared_by', 'compliance_manager')
    )

    search = request.GET.get('q', '').strip()
    if search:
        reports = reports.filter(search_q(search, (
            'document_number', 'report_type__name',
            'customer__businessName', 'distributor__businessname',
            'prospect__business_name', 'store_compliance_manager',
            'compliance_manager__name', 'prepared_by__username',
            'prepared_by__first_name', 'prepared_by__last_name',
        )))

    # Completed reports by default, as the old completed-reports page had
    # them: drafts are still being filled in, and rejected ones are void.
    # Asking for a status by name, draft or rejected included, shows it.
    status = request.GET.get('status', '').strip()
    if status == 'any':
        pass
    elif status:
        reports = reports.filter(status=status)
    else:
        reports = reports.exclude(status__in=['draft', 'rejected'])

    distributor = request.GET.get('distributor', '').strip()
    if distributor.isdigit():
        reports = reports.filter(distributor_id=int(distributor))

    # The inspection date, which is what the old page's range filtered on.
    date_from = parse_date(request.GET.get('date_from', '').strip() or '')
    if date_from:
        reports = reports.filter(inspection_date__gte=date_from)
    date_to = parse_date(request.GET.get('date_to', '').strip() or '')
    if date_to:
        reports = reports.filter(inspection_date__lte=date_to)

    report_type = request.GET.get('type', '').strip()
    if report_type.isdigit():
        reports = reports.filter(report_type_id=int(report_type))

    customer = request.GET.get('customer', '').strip()
    if customer.isdigit():
        reports = reports.filter(customer_id=int(customer))

    if request.GET.get('needs_pdf') == '1':
        reports = reports.filter(Q(pdf_file='') | Q(pdf_needs_regeneration=True))
    # The browse-PDFs grid: only reports that have one.
    if request.GET.get('has_pdf') == '1':
        reports = reports.exclude(pdf_file='').exclude(pdf_file__isnull=True)

    total = reports.count()
    try:
        page = max(1, int(request.GET.get('page', '1')))
    except ValueError:
        page = 1
    start = (page - 1) * PAGE_SIZE
    rows = reports.order_by('-created_at')[start:start + PAGE_SIZE]

    return ok({
        'reports': [_row(r) for r in rows],
        'total': total,
        'page': page,
        'page_size': PAGE_SIZE,
        'has_more': start + PAGE_SIZE < total,
    })


@staff_api
def report_detail(request, report_id):
    """One report, with every answer and the images each one carries."""
    report = get_object_or_404(
        Report.objects
        .select_related('report_type', 'customer', 'distributor', 'prospect',
                        'prepared_by', 'reviewed_by', 'compliance_manager')
        .prefetch_related(
            'answers__question__section',
            'answers__selected_options',
            'answers__attachments'),
        pk=report_id,
    )

    answers = []
    for answer in report.answers.all():
        question = answer.question
        answers.append({
            'id': answer.pk,
            'question': {
                'id': answer.question_id,
                'text': question.question_text if question else None,
                'section': (
                    question.section.name
                    if question and question.section_id else None
                ),
                'type': question.question_type if question else None,
            },
            'text': answer.text_answer,
            'number': None if answer.number_answer is None else str(answer.number_answer),
            'date': _when(answer.date_answer),
            'notes': answer.notes,
            'selected_options': [
                {'id': o.pk, 'text': o.text, 'is_flag': o.is_flag,
                 'badge_type': o.badge_type}
                for o in answer.selected_options.all()
            ],
            'file': _file(answer.file_answer),
            'signature': _file(answer.signature_answer),
            'attachments': [
                {'id': a.pk, 'caption': a.caption, 'file': _file(a.file)}
                for a in answer.attachments.all()
            ],
        })

    return ok({
        **_row(report),
        'store_compliance_manager': report.store_compliance_manager,
        'reviewed_by': report.reviewed_by.username if report.reviewed_by_id else None,
        'reviewed_at': _when(report.reviewed_at),
        'crm_pushed_at': _when(report.crm_pushed_at),
        'sales_emailed_at': _when(report.sales_emailed_at),
        'distributor': (
            {'id': report.distributor_id, 'name': report.distributor.businessname}
            if report.distributor_id else None
        ),
        'prospect': {
            'address': report.prospect.address,
            'phone': report.prospect.phone,
            'maps_link': report.prospect.maps_link,
        } if report.prospect_id else None,
        # The model's own rule for what is flagged, the one the PDF and the
        # old detail page use, so the three always agree.
        'flagged': [
            {
                'answer_id': item['answer'].pk,
                'question': item['question'].question_text,
                'section': item['section'],
                'reason': item['flag_reason'],
                'badge_type': item.get('badge_type', 'default'),
                'instructions': item.get('additional_instructions'),
            }
            for item in report.get_flagged_answers()
        ],
        'answers': answers,
    })


@staff_api
def report_types(request):
    """The report types, with how many reports and assignments each has."""
    rows = (
        ReportType.objects
        .annotate(
            report_count=Count('reports', distinct=True),
            # Withdrawing an assignment keeps its row, switched off, so
            # only the rows still on count.
            customer_count=Count(
                'customer_assignments', distinct=True,
                filter=Q(customer_assignments__is_active=True)),
            distributor_count=Count(
                'distributor_assignments', distinct=True,
                filter=Q(distributor_assignments__is_active=True)),
            section_count=Count('sections', distinct=True),
            question_count=Count('questions', distinct=True),
        )
        .order_by('name')
    )

    category = request.GET.get('category', '').strip()
    if category:
        rows = rows.filter(category=category)

    return ok({
        'report_types': [
            {
                'id': rt.pk,
                'name': rt.name,
                'description': rt.description,
                'category': rt.category,
                'prefix': rt.auto_number_prefix,
                'is_active': rt.is_active,
                'report_count': rt.report_count,
                'customer_count': rt.customer_count,
                'distributor_count': rt.distributor_count,
                'section_count': rt.section_count,
                'question_count': rt.question_count,
            }
            for rt in rows
        ],
    })


@staff_api
def generate_pdf(request, report_id):
    """Build this report's PDF, or build it again.

    Calls the model's own generate_pdf so the admin action and this endpoint
    cannot produce different documents. ?force=1 regenerates one that is
    already present, matching the admin's "regenerate" action.
    """
    if request.method != 'POST':
        return error('Use POST to generate a PDF.', status=405)

    report = get_object_or_404(Report, pk=report_id)

    if request.GET.get('force') == '1':
        report.pdf_needs_regeneration = True
        report.save(update_fields=['pdf_needs_regeneration'])

    try:
        built = report.generate_pdf()
    except Exception as exc:  # noqa: BLE001 - report the reason, never 500 silently
        return error(f'The PDF did not build: {exc}', status=500)

    if not built:
        return error('The PDF did not build.', status=500)

    report.refresh_from_db()
    return ok(_row(report))


@staff_api
def download_pdf(request, report_id):
    """Stream the report's PDF.

    The file is served through this view rather than linked directly so a
    report's PDF stays behind the staff gate.
    """
    report = get_object_or_404(Report, pk=report_id)
    if not report.pdf_file:
        raise Http404('This report has no PDF yet.')

    return FileResponse(
        report.pdf_file.open('rb'),
        content_type='application/pdf',
        filename=f'{report.document_number or report.pk}.pdf',
    )


@staff_api
def email_pdf(request, report_id):
    """Email the report's PDF to one address, building it first if needed.

    The same path the mobile app's "email PDF" uses, behind the staff gate.
    """
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email

    from .api_views import get_or_generate_report_pdf, send_report_email

    if request.method != 'POST':
        return error('POST required.', status=405)
    report = get_object_or_404(Report, pk=report_id)
    address = str(json_body(request).get('email_address') or '').strip()
    try:
        validate_email(address)
    except ValidationError:
        return error('Type a valid email address.', errors={'email_address': ['Type a valid email address.']})
    try:
        send_report_email(report, address, get_or_generate_report_pdf(report))
    except Exception as exc:  # noqa: BLE001 - say why, never 500 silently
        return error(f'The email did not send: {exc}', status=502)
    return ok({'id': report.pk, 'email_address': address})


@staff_api
def bulk_pdf(request):
    """Build the PDFs of several reports, as the admin's list action did.

    Body: {ids: [...], force: bool}. Without force, a report whose PDF is
    present and current is left alone. Answers with what happened to each.
    """
    if request.method != 'POST':
        return error('POST required.', status=405)
    body = json_body(request)
    try:
        ids = [int(pk) for pk in body.get('ids', [])]
    except (TypeError, ValueError):
        return error('ids must be report ids.')
    force = bool(body.get('force'))

    built, skipped, failed = [], [], []
    for report in Report.objects.filter(pk__in=ids):
        if not force and report.pdf_file and not report.pdf_needs_regeneration:
            skipped.append(report.pk)
            continue
        if force:
            report.pdf_needs_regeneration = True
            report.save(update_fields=['pdf_needs_regeneration'])
        try:
            (built if report.generate_pdf() else failed).append(report.pk)
        except Exception as exc:  # noqa: BLE001 - one bad report must not stop the rest
            failed.append({'id': report.pk, 'reason': str(exc)})
    return ok({'built': built, 'skipped': skipped, 'failed': failed})
