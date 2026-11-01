"""The completed-reports gaps in the admin app's reports API."""
import json
from datetime import date
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import Distributor

from .models import Answer, Prospect, Question, QuestionOption, Report, ReportType


class CompletedReportsTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('reviewer', password='pw12345678', is_staff=True)
        self.token = Token.objects.get(user=self.staff).key
        self.report_type = ReportType.objects.create(name='Audit', created_by=self.staff)
        self.distributor = Distributor.objects.create(businessname='Otago Supplies')

        def report(number, status, inspected, **extra):
            return Report.objects.create(
                report_type=self.report_type, document_number=number, prepared_by=self.staff,
                status=status, inspection_date=inspected, **extra)

        self.submitted = report('A1', 'submitted', date(2026, 3, 1), distributor=self.distributor)
        self.approved = report('A2', 'approved', date(2026, 5, 1))
        self.draft = report('A3', 'draft', date(2026, 3, 1))
        self.rejected = report('A4', 'rejected', date(2026, 3, 1))

    def call(self, name, args=(), body=None, method='post'):
        headers = {'HTTP_ACCEPT': 'application/json', 'HTTP_AUTHORIZATION': f'Token {self.token}'}
        url = reverse(f'reports:{name}', args=args)
        if method == 'get':
            return self.client.get(url, body or {}, **headers)
        return self.client.post(url, json.dumps(body or {}), content_type='application/json', **headers)

    def numbers(self, query):
        rows = self.call('staff_api_report_list', body=query, method='get').json()['data']['reports']
        return sorted(r['document_number'] for r in rows)

    def test_the_default_list_is_completed_reports_only(self):
        self.assertEqual(self.numbers({}), ['A1', 'A2'])

    def test_a_draft_or_rejected_report_is_shown_when_asked_for(self):
        self.assertEqual(self.numbers({'status': 'draft'}), ['A3'])
        self.assertEqual(self.numbers({'status': 'any'}), ['A1', 'A2', 'A3', 'A4'])

    def test_distributor_and_inspection_date_filters(self):
        self.assertEqual(self.numbers({'distributor': self.distributor.pk}), ['A1'])
        self.assertEqual(self.numbers({'date_from': '2026-04-01'}), ['A2'])
        self.assertEqual(self.numbers({'date_to': '2026-04-01'}), ['A1'])

    def test_detail_lists_flagged_answers_and_the_prospect(self):
        prospect = Prospect.objects.create(
            business_name='New Cafe', address='9 Main St', phone='03 1', maps_link='https://maps.example/x')
        self.approved.prospect = prospect
        self.approved.save()
        question = Question.objects.create(
            report_type=self.report_type, question_text='Sanitiser', question_type='radio')
        fail = QuestionOption.objects.create(
            question=question, text='FAIL', value='fail', is_flag=True, badge_type='fail',
            additional_instructions='Remake it.')
        answer = Answer.objects.create(report=self.approved, question=question)
        answer.selected_options.add(fail)

        data = self.call('staff_api_report_detail', [self.approved.pk], method='get').json()['data']

        self.assertEqual(data['prospect']['address'], '9 Main St')
        self.assertEqual(data['flagged'][0]['question'], 'Sanitiser')
        self.assertEqual(data['flagged'][0]['reason'], 'FAIL')
        self.assertEqual(data['flagged'][0]['instructions'], 'Remake it.')

    @mock.patch('reports.api_views.send_report_email')
    @mock.patch('reports.api_views.get_or_generate_report_pdf', return_value=b'%PDF')
    def test_email_checks_the_address_then_sends(self, _pdf, send):
        bad = self.call('staff_api_report_email', [self.submitted.pk], {'email_address': 'nope'})
        self.assertEqual(bad.status_code, 400)
        send.assert_not_called()

        good = self.call('staff_api_report_email', [self.submitted.pk], {'email_address': 'boss@example.com'})
        self.assertEqual(good.status_code, 200)
        send.assert_called_once_with(self.submitted, 'boss@example.com', b'%PDF')

    @mock.patch.object(Report, 'generate_pdf', return_value=True)
    def test_bulk_pdf_skips_current_pdfs_unless_forced(self, generate):
        Report.objects.filter(pk=self.approved.pk).update(pdf_file='reports/a2.pdf', pdf_needs_regeneration=False)

        data = self.call('staff_api_report_bulk_pdf', body={
            'ids': [self.submitted.pk, self.approved.pk]}).json()['data']
        self.assertEqual(data['built'], [self.submitted.pk])
        self.assertEqual(data['skipped'], [self.approved.pk])

        forced = self.call('staff_api_report_bulk_pdf', body={
            'ids': [self.approved.pk], 'force': True}).json()['data']
        self.assertEqual(forced['built'], [self.approved.pk])
