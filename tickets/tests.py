from django.test import TestCase
from django.contrib.auth.models import User

from chemsapp.models import Customer
from reports.models import (
    ReportType, ReportSection, Question, QuestionOption, Report, Answer,
)

from .models import Ticket
from .services import create_ticket_for_flagged_report


class FlaggedReportTicketTestCase(TestCase):
    # The reports app has a post_migrate signal that breaks TestCase isolation.
    serialized_rollback = True

    def setUp(self):
        self.user = User.objects.create_user(
            username='preparer', email='preparer@example.com', password='pass12345'
        )
        self.customer_user = User.objects.create_user(
            username='customer', email='customer@example.com', password='pass12345'
        )
        self.customer = Customer.objects.create(
            user=self.customer_user, businessName='Test Business', phoneNumber='555-1234',
        )
        self.report_type = ReportType.objects.create(
            name='Audit', auto_number_prefix='AUD', created_by=self.user,
        )
        self.section = ReportSection.objects.create(
            report_type=self.report_type, name='Safety', order=0,
        )
        self.question = Question.objects.create(
            report_type=self.report_type, section=self.section,
            question_text='Is the equipment compliant?', question_type='radio', order=0,
        )
        self.pass_option = QuestionOption.objects.create(
            question=self.question, text='Pass', value='pass', is_flag=False,
        )
        self.fail_option = QuestionOption.objects.create(
            question=self.question, text='Fail', value='fail', is_flag=True,
            badge_type='fail', additional_instructions='Schedule remediation.',
        )

    def _make_report(self, customer=None):
        return Report.objects.create(
            report_type=self.report_type, customer=customer,
            inspection_date='2026-05-31', prepared_by=self.user, status='draft',
        )

    def _flag(self, report):
        answer = Answer.objects.create(report=report, question=self.question)
        answer.selected_options.add(self.fail_option)
        return answer

    def test_creates_ticket_for_flagged_report(self):
        report = self._make_report(customer=self.customer)
        self._flag(report)

        ticket = create_ticket_for_flagged_report(report)

        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.ticket_type, 'flagged_report')
        self.assertIsNone(ticket.assigned_to)
        self.assertEqual(ticket.source_report, report)
        self.assertEqual(ticket.created_by, self.user)
        self.assertEqual(ticket.customer, self.customer)
        self.assertIn(report.document_number, ticket.subject)
        # Body summarizes the flagged item, reason, and instructions.
        self.assertIn('Is the equipment compliant?', ticket.body)
        self.assertIn('Fail', ticket.body)
        self.assertIn('Schedule remediation.', ticket.body)

    def test_idempotent_no_duplicate_on_resubmit(self):
        report = self._make_report(customer=self.customer)
        self._flag(report)

        first = create_ticket_for_flagged_report(report)
        second = create_ticket_for_flagged_report(report)

        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(
            Ticket.objects.filter(source_report=report, ticket_type='flagged_report').count(), 1,
        )

    def test_no_ticket_when_nothing_flagged(self):
        report = self._make_report(customer=self.customer)
        answer = Answer.objects.create(report=report, question=self.question)
        answer.selected_options.add(self.pass_option)

        ticket = create_ticket_for_flagged_report(report)

        self.assertIsNone(ticket)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_ticket_created_when_report_has_no_customer(self):
        report = self._make_report(customer=None)
        self._flag(report)

        ticket = create_ticket_for_flagged_report(report)

        self.assertIsNotNone(ticket)
        self.assertIsNone(ticket.customer)

    def test_mark_submitted_creates_ticket(self):
        """mark_submitted() is the single entry point used by all submission
        paths; it should set status and create the flagged-item ticket."""
        report = self._make_report(customer=self.customer)
        self._flag(report)

        report.mark_submitted()

        report.refresh_from_db()
        self.assertEqual(report.status, 'submitted')
        self.assertIsNotNone(report.submitted_at)
        self.assertEqual(
            Ticket.objects.filter(source_report=report, ticket_type='flagged_report').count(), 1,
        )
