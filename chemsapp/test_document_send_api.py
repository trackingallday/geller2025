"""The Send documents API, as the admin app calls it. Postmark is mocked."""
import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import DocumentSend, Product, ProductDocument

SEND = 'chemsapp.document_api_views._send_one'


class DocumentSendApiTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            'send-staff', password='pw12345678', is_staff=True, email='dana@geller.co.nz')
        self.auth = {'HTTP_AUTHORIZATION': f'Token {Token.objects.get(user=self.staff).key}'}
        self.both = Product.objects.create(
            name='Citrus Degreaser', description='d', directions='d', productCode='CD1',
            sdsSheet='documents/cd-sds.pdf', infoSheet='documents/cd-info.pdf')
        self.sds_only = Product.objects.create(
            name='Glass Clean', description='d', directions='d', productCode='GC1',
            sdsSheet='documents/gc-sds.pdf')
        self.url = reverse('staff_api_document_send_list')

    def post(self, payload):
        return self.client.post(self.url, json.dumps(payload), content_type='application/json', **self.auth)

    def payload(self, **overrides):
        payload = {
            'emails': ['Buyer@Example.com', 'buyer@example.com', 'ops@example.com'],
            'items': [{'product': self.both.pk, 'kinds': ['sds', 'info']},
                      {'product': self.sds_only.pk, 'kinds': ['sds']}],
            'message': 'Here are the sheets.',
        }
        payload.update(overrides)
        return payload

    def test_non_staff_is_refused(self):
        plain = User.objects.create_user('send-plain', password='pw12345678')
        response = self.client.get(self.url, HTTP_AUTHORIZATION=f'Token {Token.objects.get(user=plain).key}')
        self.assertEqual(response.status_code, 403)

    @mock.patch(SEND)
    def test_send_mails_each_address_once_and_records_versions(self, send_one):
        response = self.post(self.payload())
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()['data']
        self.assertEqual(data['recipients'], ['buyer@example.com', 'ops@example.com'])
        self.assertEqual(send_one.call_count, 2)
        email, subject, body, reply_to = send_one.call_args_list[0].args
        self.assertEqual(email, 'buyer@example.com')
        self.assertEqual(reply_to, 'dana@geller.co.nz')
        self.assertIn('Here are the sheets.', body)
        self.assertIn(f'/product_download/{self.both.pk}/sds/', body)
        self.assertIn(f'/product_download/{self.both.pk}/info/', body)
        self.assertIn(f'/product_download/{self.sds_only.pk}/sds/', body)

        self.assertEqual(len(data['items']), 3)
        current = ProductDocument.objects.get(product=self.both, kind='sds')
        sds_item = next(i for i in data['items'] if i['product_id'] == self.both.pk and i['kind'] == 'sds')
        self.assertEqual(sds_item['document_id'], current.pk)
        self.assertEqual(response.json()['failed'], [])

        listed = self.client.get(self.url, **self.auth).json()['data']
        self.assertEqual(len(listed), 1)
        versions = self.client.get(
            reverse('staff_api_product_document_list', args=[self.both.pk]), **self.auth).json()['data']
        self.assertEqual(versions['documents']['sds'][0]['send_count'], 1)

    @mock.patch(SEND)
    def test_missing_file_is_refused(self, send_one):
        response = self.post(self.payload(items=[{'product': self.sds_only.pk, 'kinds': ['info']}]))
        self.assertEqual(response.status_code, 400)
        self.assertIn('items', response.json()['errors'])
        send_one.assert_not_called()
        self.assertFalse(DocumentSend.objects.exists())

    @mock.patch(SEND)
    def test_bad_fields_are_refused(self, send_one):
        for payload in (
            self.payload(emails=['not-an-email']),
            self.payload(emails=[]),
            self.payload(items=[]),
            self.payload(items=[{'product': 999999, 'kinds': ['sds']}]),
            self.payload(items=[{'product': self.both.pk, 'kinds': ['mpi_approval']}]),
            self.payload(items=[{'product': self.both.pk, 'kinds': []}]),
        ):
            response = self.post(payload)
            self.assertEqual(response.status_code, 400, payload)
        send_one.assert_not_called()

    @mock.patch(SEND, side_effect=[None, RuntimeError('down')])
    def test_partial_failure_records_only_the_sent_addresses(self, send_one):
        response = self.post(self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['recipients'], ['buyer@example.com'])
        self.assertEqual(response.json()['failed'], ['ops@example.com'])

    @mock.patch(SEND, side_effect=RuntimeError('down'))
    def test_total_failure_gives_502_and_no_record(self, send_one):
        response = self.post(self.payload())
        self.assertEqual(response.status_code, 502)
        self.assertFalse(DocumentSend.objects.exists())

    @mock.patch(SEND)
    def test_list_filters_by_product_and_email(self, send_one):
        self.post(self.payload(emails=['a@example.com'], items=[{'product': self.both.pk, 'kinds': ['sds']}]))
        self.post(self.payload(emails=['b@example.com'], items=[{'product': self.sds_only.pk, 'kinds': ['sds']}]))
        by_product = self.client.get(self.url, {'product': self.both.pk}, **self.auth).json()['data']
        self.assertEqual([s['recipients'] for s in by_product], [['a@example.com']])
        by_email = self.client.get(self.url, {'q': 'B@exa'}, **self.auth).json()['data']
        self.assertEqual([s['recipients'] for s in by_email], [['b@example.com']])
