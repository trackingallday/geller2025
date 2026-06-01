"""Service helpers for the tickets app."""
import logging

from .models import Ticket

logger = logging.getLogger('django')


def _build_flagged_body(report, flagged_answers):
    """Build a human-readable summary of a report's flagged items."""
    lines = [
        f"This ticket was created automatically because report "
        f"\"{report.document_number}\" ({report.report_type.name}) was submitted "
        f"with {len(flagged_answers)} flagged item(s).",
        "",
    ]
    if report.customer:
        lines.append(f"Customer: {report.customer.businessName}")
    lines.append(f"Inspection date: {report.inspection_date}")
    lines.append("")
    lines.append("Flagged items:")

    for index, item in enumerate(flagged_answers, start=1):
        question = item['question']
        lines.append("")
        lines.append(f"{index}. [{item['section']}] {question.question_text}")
        lines.append(f"   Answer: {item['display_value']}")
        if item.get('flag_reason'):
            lines.append(f"   Reason: {item['flag_reason']}")
        if item.get('additional_instructions'):
            lines.append(f"   Instructions: {item['additional_instructions']}")

    return "\n".join(lines)


def create_ticket_for_flagged_report(report):
    """Create one unassigned 'flagged_report' ticket summarizing a report's
    flagged items.

    No-op (returns None) if the report has no flagged items or a flagged
    ticket already exists for it. Returns the created Ticket otherwise.
    """
    flagged_answers = report.get_flagged_answers()
    if not flagged_answers:
        return None

    # Idempotency: don't duplicate if a flagged ticket already exists for this report.
    if Ticket.objects.filter(source_report=report, ticket_type='flagged_report').exists():
        return None

    ticket = Ticket.objects.create(
        created_by=report.prepared_by,
        customer=report.customer,
        assigned_to=None,
        ticket_type='flagged_report',
        source_report=report,
        status='pending',
        subject=f"Flagged items: {report.document_number}",
        body=_build_flagged_body(report, flagged_answers),
    )
    logger.info(
        "Created flagged-report ticket #%s for report %s (%s flagged items)",
        ticket.pk, report.document_number, len(flagged_answers),
    )
    return ticket
