"""Service helpers for routing Site Assessment report submissions to sales.

Both functions here are called once, best-effort, from Report.mark_submitted()
for reports whose ReportType.category is 'site_assessment'. The caller is
responsible for catching exceptions and recording success (see
Report.crm_pushed_at / Report.sales_emailed_at) so retries don't duplicate
the CRM contact or the email.
"""
import logging

from django.conf import settings

from chemsapp.onepagecrm import create_contact_with_note

logger = logging.getLogger('django')


def _build_assessment_note(report):
    """Build the note text attached to the OnePageCRM contact for this report."""
    lines = [
        f"Site Assessment submitted via geller.co.nz: {report.report_type.name}",
        f"Document number: {report.document_number}",
        f"Inspection date: {report.inspection_date}",
    ]
    if report.prospect:
        if report.prospect.address:
            lines.append(f"Address: {report.prospect.address}")
        if report.prospect.phone:
            lines.append(f"Phone: {report.prospect.phone}")
        if report.prospect.maps_link:
            lines.append(f"Maps link: {report.prospect.maps_link}")
        if report.prospect.notes:
            lines.append(f"Notes: {report.prospect.notes}")

    flagged_answers = report.get_flagged_answers()
    if flagged_answers:
        lines.append('')
        lines.append(f"Flagged items ({len(flagged_answers)}):")
        for item in flagged_answers:
            lines.append(f"- [{item['section']}] {item['question'].question_text}: {item['display_value']}")

    return '\n'.join(lines)


def push_site_assessment_to_onepagecrm(report):
    """Push a submitted Site Assessment report into OnePageCRM as a lead:
    a contact tagged with the report type, plus a note summarizing the visit.

    Raises on failure — the caller (Report.mark_submitted) catches and logs.
    """
    prospect = report.prospect
    business_name = prospect.business_name if prospect else (
        report.customer.businessName if report.customer else 'Unknown business'
    )
    phone = prospect.phone if prospect else ''

    contact_id = create_contact_with_note(
        name=business_name,
        email='',
        note_text=_build_assessment_note(report),
        tags=[f'Site Assessment: {report.report_type.name}'],
        company_name=business_name,
    )
    logger.info(
        "OnePageCRM site assessment push OK: contact %s, report %s",
        contact_id, report.document_number,
    )
    return contact_id


def email_site_assessment_to_sales(report):
    """Email a submitted Site Assessment report (with PDF) to the sales inbox.

    Recipient is SITE_ASSESSMENT_SALES_EMAIL (settings) so it can be pointed
    at sales@geller.co.nz in production without a code change. Raises on
    failure — the caller (Report.mark_submitted) catches and logs.
    """
    from .api_views import send_report_email

    pdf_file = report.get_or_generate_pdf()
    with pdf_file.open('rb') as f:
        pdf_content = f.read()

    recipient = settings.SITE_ASSESSMENT_SALES_EMAIL
    send_report_email(report, recipient, pdf_content)
    logger.info(
        "Site assessment report %s emailed to %s", report.document_number, recipient,
    )
