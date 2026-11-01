"""The JSON contract the admin app relies on, for the dashboard writes.

Each test sends what the admin app sends (a JSON Accept header and a token)
and checks the shape that comes back. The old templates send different
headers and must keep their own shapes, so those are checked too.
"""
import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import (
    ApplicationType, Customer, CustomerGroup, GroupPricingVariant,
    PricingVariant, Product, ProductVariant, Size,
)


class ContractTestCase(TestCase):
    """A staff token, and helpers that call the way the admin app does."""

    def setUp(self):
        self.staff = User.objects.create_user(
            'staffer', password='pw12345678', is_staff=True)
        # A post_save signal makes the token, so read it rather than create it.
        self.token = Token.objects.get(user=self.staff).key
        self.product = Product.objects.create(
            name='Clean Green HD', description='d', directions='d',
            productCode='CLEANO5')
        self.size = Size.objects.create(
            name='5L', desc='5 litre', amount='5', volume_litres='5.000')
        self.variant = ProductVariant.objects.create(
            product=self.product, size=self.size, pack_size=1, code='CLEANO5-5L')

    def app_post(self, url, data=None, **extra):
        """POST as the admin app does: JSON in, JSON wanted, token auth."""
        return self.client.post(
            url, data=json.dumps(data or {}), content_type='application/json',
            HTTP_ACCEPT='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token}', **extra)

    def app_get(self, url):
        return self.client.get(
            url, HTTP_ACCEPT='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token}')


class VariantSaveContractTests(ContractTestCase):
    def test_app_gets_the_standard_envelope_on_success(self):
        response = self.app_post(
            reverse('save_one_variant', args=[self.variant.pk]),
            {'code': 'CLEANO5-5L-NEW', 'size': self.size.pk, 'pack_size': 1, 'barcode': '9421033275684'})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['ok'])
        # The variant is under `data`, like every other endpoint, so the
        # app's apiFetch unwraps it the same way.
        self.assertEqual(body['data']['code'], 'CLEANO5-5L-NEW')
        self.assertNotIn('variant', body)

    def test_app_gets_plain_string_field_errors(self):
        response = self.app_post(
            reverse('save_one_variant', args=[self.variant.pk]),
            {'code': 'X', 'size': 999999, 'pack_size': 1, 'barcode': '9421033275684'})

        self.assertEqual(response.status_code, 400)
        errors = response.json()['errors']
        self.assertIn('size', errors)
        self.assertIsInstance(errors['size'][0], str)

    def test_old_template_fetch_keeps_its_own_shape(self):
        # The template posts a form with X-Requested-With and no JSON Accept.
        self.client.login(username='staffer', password='pw12345678')
        response = self.client.post(
            reverse('save_one_variant', args=[self.variant.pk]),
            {'code': 'CLEANO5-5L', 'size': self.size.pk, 'pack_size': 1, 'barcode': '9421033275684'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        body = response.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['variant']['id'], self.variant.pk)

    def test_create_variant_returns_the_new_row(self):
        response = self.app_post(
            reverse('create_variant', args=[self.product.pk]),
            {'code': 'CLEANO5-20L', 'size': self.size.pk, 'pack_size': 1, 'barcode': '9421033275684'})

        self.assertEqual(response.status_code, 200)
        new_id = response.json()['data']['id']
        self.assertTrue(ProductVariant.objects.filter(
            pk=new_id, product=self.product).exists())


class FormsetErrorContractTests(ContractTestCase):
    def test_dilution_errors_are_keyed_by_row_and_field(self):
        prefix = f'dilution-{self.variant.pk}'
        response = self.app_post(
            reverse('save_dilutions', args=[self.variant.pk]),
            {
                f'{prefix}-TOTAL_FORMS': '1',
                f'{prefix}-INITIAL_FORMS': '0',
                f'{prefix}-0-application_type': '999999',
                f'{prefix}-0-value': '10',
            })

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body['detail'], 'The dilutions did not save.')
        # Row 0's bad application type, not a list of mostly empty dicts.
        self.assertIn('0.application_type', body['errors'])
        self.assertIsInstance(body['errors']['0.application_type'][0], str)

    def test_contact_errors_are_keyed_by_row_and_field(self):
        user = User.objects.create(username='cust', email='c@example.com')
        customer = Customer.objects.create(
            user=user, phoneNumber='1', businessName='Uno', address='1 Road')

        response = self.app_post(
            reverse('save_customer_contacts', args=[customer.pk]),
            {
                'contacts-TOTAL_FORMS': '1',
                'contacts-INITIAL_FORMS': '0',
                'contacts-0-name': 'Sam',
                'contacts-0-email': 'not-an-email',
            })

        self.assertEqual(response.status_code, 400)
        self.assertIn('0.email', response.json()['errors'])

    def test_a_valid_formset_still_saves(self):
        kind = ApplicationType.objects.create(name='Spray bottle')
        prefix = f'dilution-{self.variant.pk}'
        response = self.app_post(
            reverse('save_dilutions', args=[self.variant.pk]),
            {
                f'{prefix}-TOTAL_FORMS': '1',
                f'{prefix}-INITIAL_FORMS': '0',
                f'{prefix}-0-application_type': str(kind.pk),
                f'{prefix}-0-value': '10',
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.variant.dilutions.count(), 1)


class GellerAiSyncContractTests(ContractTestCase):
    def test_a_json_body_reaches_the_pdf_option(self):
        with mock.patch(
            'chemsapp.product_dashboard_views._sync_product_to_geller_ai',
            return_value={'ok': True},
        ) as sync:
            self.app_post(
                reverse('sync_product_to_geller_ai', args=[self.product.pk]),
                {'include_pdfs': True})

        # The third argument is include_pdfs. It used to read request.POST,
        # which is empty for a JSON body, so this was always False.
        self.assertIs(sync.call_args.args[2], True)

    def test_a_failure_carries_detail_for_the_app_and_error_for_the_template(self):
        import requests

        with mock.patch(
            'chemsapp.product_dashboard_views._sync_product_to_geller_ai',
            side_effect=requests.Timeout,
        ):
            response = self.app_post(
                reverse('sync_product_to_geller_ai', args=[self.product.pk]))

        self.assertEqual(response.status_code, 504)
        body = response.json()
        self.assertEqual(body['detail'], body['error'])


class ReadApiFieldTests(ContractTestCase):
    def test_variant_prices_carry_name_and_minimum_quantity(self):
        PricingVariant.objects.create(
            product_variant=self.variant, price='10.00', name='Trade', min_quantity=5)
        group = CustomerGroup.objects.create(name='Cafes')
        GroupPricingVariant.objects.create(
            product_variant=self.variant, customer_group=group, price='9.00',
            name='Cafe rate', min_quantity=2)

        data = self.app_get(
            reverse('staff_api_variant_detail', args=[self.variant.pk])).json()['data']

        self.assertEqual(data['customer_prices'][0]['name'], 'Trade')
        self.assertEqual(data['group_prices'][0]['name'], 'Cafe rate')
        self.assertEqual(data['group_prices'][0]['min_quantity'], 2)

    def test_group_prices_carry_name_and_minimum_quantity(self):
        group = CustomerGroup.objects.create(name='Cafes')
        GroupPricingVariant.objects.create(
            product_variant=self.variant, customer_group=group, price='9.00',
            name='Cafe rate', min_quantity=2)

        data = self.app_get(
            reverse('staff_api_group_detail', args=[group.pk])).json()['data']

        self.assertEqual(data['prices'][0]['name'], 'Cafe rate')
        self.assertEqual(data['prices'][0]['min_quantity'], 2)

    def test_reference_data_lists_sizes_for_the_variant_form(self):
        data = self.app_get(reverse('staff_api_reference_data')).json()['data']

        self.assertIn({'id': self.size.pk, 'name': '5L'}, data['sizes'])
