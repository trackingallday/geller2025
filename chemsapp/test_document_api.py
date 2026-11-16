"""The product document versions API, as the admin app calls it."""
import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import Product, ProductDocument, ProductVariant


def pdf(name='sheet.pdf'):
    return SimpleUploadedFile(name, b'%PDF-1.4 test', content_type='application/pdf')


class DocumentApiTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            'docs-staff', password='pw12345678', is_staff=True, first_name='Dana', last_name='Lee')
        self.auth = {'HTTP_AUTHORIZATION': f'Token {Token.objects.get(user=self.staff).key}'}
        self.product = Product.objects.create(
            name='Citrus Degreaser', description='d', directions='d', productCode='CD1',
            sdsSheet='documents/sds-old.pdf')
        self.variant = ProductVariant.objects.create(product=self.product, code='CD1-5', pack_size=1)
        self.list_url = reverse('staff_api_product_document_list', args=[self.product.pk])

    def detail_url(self, document):
        return reverse('staff_api_product_document_detail', args=[document.pk])

    def upload(self, **fields):
        return self.client.post(self.list_url, fields, **self.auth)

    def test_non_staff_is_refused(self):
        plain = User.objects.create_user('docs-plain', password='pw12345678')
        token = Token.objects.get(user=plain).key
        response = self.client.get(self.list_url, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 403)

    def test_list_groups_versions_by_kind_and_size(self):
        data = self.client.get(self.list_url, **self.auth).json()['data']
        self.assertEqual(len(data['documents']['sds']), 1)
        self.assertTrue(data['documents']['sds'][0]['is_current'])
        self.assertEqual(data['documents']['info'], [])
        self.assertEqual(data['labels'][0]['variant_id'], self.variant.pk)
        self.assertEqual(data['labels'][0]['versions'], [])

    def test_upload_makes_the_new_version_current(self):
        response = self.upload(kind='sds', file=pdf('sds-v2.pdf'), version='2.0', issued_on='2026-11-01')
        self.assertEqual(response.status_code, 200)
        body = response.json()['data']
        self.assertTrue(body['is_current'])
        self.assertEqual(body['version'], '2.0')
        self.assertEqual(body['issued_on'], '2026-11-01')
        self.assertEqual(body['uploaded_by'], 'Dana Lee')
        self.product.refresh_from_db()
        self.assertEqual(self.product.sdsSheet.name, ProductDocument.objects.get(pk=body['id']).file.name)
        # The old version stays, and the signal made no duplicate.
        self.assertEqual(ProductDocument.objects.filter(product=self.product, kind='sds').count(), 2)

    def test_upload_of_a_label_sets_the_size_label(self):
        response = self.upload(kind='label', file=pdf('label.pdf'), variant=self.variant.pk)
        self.assertEqual(response.status_code, 200)
        self.variant.refresh_from_db()
        self.assertTrue(self.variant.label.name.startswith('documents/label'))
        self.assertEqual(ProductDocument.objects.filter(kind='label').count(), 1)

    def test_label_without_a_size_is_refused(self):
        response = self.upload(kind='label', file=pdf())
        self.assertEqual(response.status_code, 400)
        self.assertIn('variant', response.json()['errors'])

    def test_label_for_a_size_of_another_product_is_refused(self):
        other = Product.objects.create(name='Other', description='d', directions='d', productCode='O1')
        other_variant = ProductVariant.objects.create(product=other, code='O1-5', pack_size=1)
        response = self.upload(kind='label', file=pdf(), variant=other_variant.pk)
        self.assertEqual(response.status_code, 400)

    def test_upload_without_a_file_gives_field_errors(self):
        response = self.upload(kind='info')
        self.assertEqual(response.status_code, 400)
        self.assertIn('file', response.json()['errors'])

    def test_bad_date_gives_field_errors(self):
        response = self.upload(kind='info', file=pdf(), issued_on='not-a-date')
        self.assertEqual(response.status_code, 400)
        self.assertIn('issued_on', response.json()['errors'])

    def test_edit_changes_only_the_fields_sent(self):
        document = ProductDocument.objects.get(product=self.product, kind='sds')
        self.client.post(
            self.detail_url(document), json.dumps({'version': '1.0'}),
            content_type='application/json', **self.auth)
        self.client.post(
            self.detail_url(document), json.dumps({'issued_on': '2025-02-03'}),
            content_type='application/json', **self.auth)
        document.refresh_from_db()
        self.assertEqual(document.version, '1.0')
        self.assertEqual(document.issued_on.isoformat(), '2025-02-03')

    def test_the_current_version_cannot_be_deleted(self):
        document = ProductDocument.objects.get(product=self.product, kind='sds')
        response = self.client.delete(self.detail_url(document), **self.auth)
        self.assertEqual(response.status_code, 409)
        self.assertTrue(ProductDocument.objects.filter(pk=document.pk).exists())

    def test_an_old_version_can_be_deleted(self):
        old = ProductDocument.objects.get(product=self.product, kind='sds')
        self.upload(kind='sds', file=pdf('sds-v2.pdf'))
        response = self.client.delete(self.detail_url(old), **self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ProductDocument.objects.filter(pk=old.pk).exists())
        self.product.refresh_from_db()
        self.assertTrue(self.product.sdsSheet.name.startswith('documents/sds-v2'))
