"""The report-types list of the admin app: its counts, and its query count."""
from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import Customer, Distributor

from .models import (
    Question, Report, ReportSection, ReportType, ReportTypeCustomer,
    ReportTypeDistributor,
)


class ReportTypesListTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('rt-list', password='pw12345678', is_staff=True)
        self.auth = {'HTTP_AUTHORIZATION': f'Token {Token.objects.get(user=self.staff).key}'}
        self.audit = ReportType.objects.create(
            name='Monthly Audit', category='standard', created_by=self.staff)
        self.empty = ReportType.objects.create(
            name='Blank', category='site_assessment', created_by=self.staff)

        # Two of each row, so that a join product shows as a wrong count.
        for number in range(2):
            section = ReportSection.objects.create(
                report_type=self.audit, name=f'Section {number}', order=number)
            Question.objects.create(
                report_type=self.audit, section=section,
                question_text=f'Question {number}', question_type='text')
            Report.objects.create(
                report_type=self.audit, document_number=f'MA{number}', prepared_by=self.staff)
            user = User.objects.create(username=f'cafe{number}')
            customer = Customer.objects.create(
                user=user, phoneNumber='1', businessName=f'Cafe {number}', address='1 Road')
            ReportTypeCustomer.objects.create(report_type=self.audit, customer=customer)
            distributor = Distributor.objects.create(businessname=f'Supplier {number}')
            ReportTypeDistributor.objects.create(report_type=self.audit, distributor=distributor)
        Question.objects.create(
            report_type=self.audit, question_text='No section', question_type='text')
        # A withdrawn assignment keeps its row, but does not count.
        withdrawn = Customer.objects.create(
            user=User.objects.create(username='gone'), phoneNumber='1',
            businessName='Gone', address='1 Road')
        ReportTypeCustomer.objects.create(
            report_type=self.audit, customer=withdrawn, is_active=False)

    def get(self, **params):
        url = reverse('reports:staff_api_report_types')
        return self.client.get(url, params, **self.auth).json()['data']['report_types']

    def test_counts_each_relation_on_its_own(self):
        rows = {row['name']: row for row in self.get()}
        audit = rows['Monthly Audit']
        self.assertEqual(audit['report_count'], 2)
        self.assertEqual(audit['customer_count'], 2)
        self.assertEqual(audit['distributor_count'], 2)
        self.assertEqual(audit['section_count'], 2)
        self.assertEqual(audit['question_count'], 3)

    def test_a_type_with_nothing_counts_zero(self):
        blank = {row['name']: row for row in self.get()}['Blank']
        for key in ('report_count', 'customer_count', 'distributor_count',
                    'section_count', 'question_count'):
            self.assertEqual(blank[key], 0, key)

    def test_category_filter(self):
        self.assertEqual([row['name'] for row in self.get(category='site_assessment')], ['Blank'])

    def test_one_query_for_the_list(self):
        url = reverse('reports:staff_api_report_types')
        self.client.get(url, **self.auth)  # The token lookup warms up here.
        with CaptureQueriesContext(connection) as queries:
            self.client.get(url, **self.auth)
        list_queries = [q for q in queries if 'reports_reporttype' in q['sql']
                        and 'authtoken' not in q['sql']]
        self.assertEqual(len(list_queries), 1)
        # No join from the type to its rows: each count is a subquery.
        self.assertNotIn('LEFT OUTER JOIN', list_queries[0]['sql'])
