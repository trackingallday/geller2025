"""The application-types JSON API, as the admin app calls it."""
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import ApplicationType, DilutionVariant, Product, ProductVariant


class ApplicationTypeApiTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('types-staff', password='pw12345678', is_staff=True)
        self.auth = {'HTTP_AUTHORIZATION': f'Token {Token.objects.get(user=self.staff).key}'}
        self.spray = ApplicationType.objects.create(
            name='Spray bottle', category='Spray Bottle', unit_label='per bottle',
            unit_volume_litres='0.750', sort_order=2)
        self.mop = ApplicationType.objects.create(
            name='Mop bucket', category='Floors', unit_label='per bucket', sort_order=1)
        self.list_url = reverse('staff_api_application_type_list')

    def detail_url(self, application_type):
        return reverse('staff_api_application_type_detail', args=[application_type.pk])

    def post_json(self, url, payload):
        return self.client.post(
            url, json.dumps(payload), content_type='application/json', **self.auth)

    def test_non_staff_is_refused(self):
        plain = User.objects.create_user('types-plain', password='pw12345678')
        token = Token.objects.get(user=plain).key
        response = self.client.get(self.list_url, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 403)

    def test_list_is_in_sort_order_with_value_kinds(self):
        data = self.client.get(self.list_url, **self.auth).json()['data']
        names = [item['name'] for item in data['application_types']]
        self.assertEqual(names, ['Mop bucket', 'Spray bottle'])
        self.assertEqual(data['application_types'][1]['unit_volume_litres'], '0.750')
        self.assertIn('ratio', [kind['value'] for kind in data['value_kinds']])

    def test_list_search(self):
        data = self.client.get(self.list_url, {'q': 'floors'}, **self.auth).json()['data']
        self.assertEqual([item['name'] for item in data['application_types']], ['Mop bucket'])

    def test_create(self):
        response = self.post_json(self.list_url, {
            'name': 'Dishwasher', 'value_kind': 'ml_per_cycle',
            'unit_label': 'per cycle', 'sort_order': 3, 'is_active': True,
        })
        self.assertEqual(response.status_code, 200)
        created = ApplicationType.objects.get(name='Dishwasher')
        self.assertEqual(created.value_kind, 'ml_per_cycle')
        self.assertIsNone(created.unit_volume_litres)

    def test_create_with_a_duplicate_name_gives_field_errors(self):
        response = self.post_json(self.list_url, {'name': 'Spray bottle', 'unit_label': 'x'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.json()['errors'])

    def test_partial_update_keeps_the_other_fields(self):
        response = self.post_json(self.detail_url(self.spray), {'is_active': False})
        self.assertEqual(response.status_code, 200)
        self.spray.refresh_from_db()
        self.assertFalse(self.spray.is_active)
        self.assertEqual(self.spray.unit_label, 'per bottle')
        self.assertEqual(self.spray.sort_order, 2)

    def test_partial_update_of_sort_order_keeps_is_active(self):
        self.post_json(self.detail_url(self.spray), {'sort_order': 9})
        self.spray.refresh_from_db()
        self.assertEqual(self.spray.sort_order, 9)
        self.assertTrue(self.spray.is_active)

    def test_delete_an_unused_type(self):
        response = self.client.delete(self.detail_url(self.mop), **self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ApplicationType.objects.filter(pk=self.mop.pk).exists())

    def test_delete_a_type_in_use_is_refused(self):
        product = Product.objects.create(
            name='Zeal', description='d', directions='d', productCode='ZE')
        variant = ProductVariant.objects.create(product=product, pack_size=1, code='ZE1')
        DilutionVariant.objects.create(variant=variant, application_type=self.spray, value='50')
        response = self.client.delete(self.detail_url(self.spray), **self.auth)
        self.assertEqual(response.status_code, 409)
        self.assertTrue(ApplicationType.objects.filter(pk=self.spray.pk).exists())
        detail = self.client.get(self.detail_url(self.spray), **self.auth).json()['data']
        self.assertEqual(detail['dilution_count'], 1)
