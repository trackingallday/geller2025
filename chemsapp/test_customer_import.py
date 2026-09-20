"""Tests for the customers spreadsheet importer and its dashboard upload."""
from io import BytesIO

import openpyxl
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from chemsapp.customers_import import import_customers_workbook
from chemsapp.models import Customer, CustomerContact


def make_workbook(customer_rows, user_rows):
    """An in-memory .xlsx with a "Customers" sheet and a "Users" sheet.

    customer_rows: list of (businessName, phoneNumber, address, group).
    user_rows: list of (Customer, first_name, last_name, email).
    """
    workbook = openpyxl.Workbook()
    customers_sheet = workbook.active
    customers_sheet.title = 'Customers'
    customers_sheet.append(['businessName', 'phoneNumber', 'address', 'group'])
    for row in customer_rows:
        customers_sheet.append(list(row))

    users_sheet = workbook.create_sheet('Users')
    users_sheet.append(['Customer', 'First Name', 'Last Name', 'Email Address'])
    for row in user_rows:
        users_sheet.append(list(row))

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


class ImportCustomersWorkbookTests(TestCase):
    def test_creates_user_customer_and_contact(self):
        workbook = make_workbook(
            [('Acme Ltd', '123', '1 Road', 1)],
            [('Acme Ltd', 'Jane', 'Doe', 'jane@example.com')],
        )
        stats = import_customers_workbook(workbook)

        self.assertEqual(len(stats['created']), 1)
        self.assertEqual(stats['skipped_existing'], [])
        self.assertEqual(stats['errors'], [])

        user = User.objects.get(email='jane@example.com')
        self.assertEqual(user.username, 'jane@example.com')
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Doe')
        self.assertTrue(user.has_usable_password())

        customer = Customer.objects.get(user=user)
        self.assertEqual(customer.businessName, 'Acme Ltd')
        self.assertEqual(customer.phoneNumber, '123')
        self.assertEqual(customer.address, '1 Road')
        self.assertIsNone(customer.group)
        self.assertFalse(customer.hasSetPassword)

        contact = CustomerContact.objects.get(customer=customer)
        self.assertEqual(contact.name, 'Jane Doe')
        self.assertEqual(contact.email, 'jane@example.com')

    def test_skips_a_row_whose_email_already_has_an_account(self):
        User.objects.create_user(username='jane@example.com', email='jane@example.com')
        workbook = make_workbook(
            [('Acme Ltd', '123', '1 Road', 1)],
            [('Acme Ltd', 'Jane', 'Doe', 'jane@example.com')],
        )
        stats = import_customers_workbook(workbook)

        self.assertEqual(stats['created'], [])
        self.assertEqual(len(stats['skipped_existing']), 1)
        self.assertFalse(Customer.objects.exists())

    def test_row_with_no_matching_contact_is_an_error(self):
        workbook = make_workbook(
            [('Acme Ltd', '123', '1 Road', 1)],
            [],
        )
        stats = import_customers_workbook(workbook)

        self.assertEqual(stats['created'], [])
        self.assertEqual(len(stats['errors']), 1)
        self.assertIn('Acme Ltd', stats['errors'][0])

    def test_blank_last_name_is_not_an_error(self):
        workbook = make_workbook(
            [('Acme Ltd', '123', '1 Road', 1)],
            [('Acme Ltd', 'FSNI', '', 'fsni@example.com')],
        )
        stats = import_customers_workbook(workbook)

        self.assertEqual(len(stats['created']), 1)
        contact = CustomerContact.objects.get()
        self.assertEqual(contact.name, 'FSNI')


class ImportCustomersViewTests(TestCase):
    def setUp(self):
        self.url = reverse('import_customers')
        User.objects.create_user('staffer', password='pw12345678', is_staff=True)
        self.client.login(username='staffer', password='pw12345678')

    def _upload(self, dry_run):
        workbook = make_workbook(
            [('Acme Ltd', '123', '1 Road', 1)],
            [('Acme Ltd', 'Jane', 'Doe', 'jane@example.com')],
        )
        upload = SimpleUploadedFile(
            'customers.xlsx', workbook.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        data = {'workbook': upload}
        if dry_run:
            data['dry_run'] = '1'
        return self.client.post(self.url, data)

    def test_signed_out_user_is_sent_to_login(self):
        self.client.logout()
        response = self._upload(dry_run=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_dry_run_reports_but_saves_nothing(self):
        response = self._upload(dry_run=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='jane@example.com').exists())
        self.assertFalse(Customer.objects.exists())

    def test_real_run_saves_the_customer(self):
        response = self._upload(dry_run=False)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email='jane@example.com').exists())
        self.assertEqual(Customer.objects.count(), 1)

    def test_missing_file_shows_an_error_without_crashing(self):
        response = self.client.post(self.url, {'dry_run': '1'})
        self.assertEqual(response.status_code, 200)
