"""Tests for the version history of product documents (ProductDocument)."""

import importlib

from django.apps import apps
from django.test import TestCase

from chemsapp.models import (
    DocumentSend, DocumentSendItem, Product, ProductDocument, ProductVariant,
)

backfill_migration = importlib.import_module('chemsapp.migrations.0035_backfill_product_documents')


def make_product(**fields):
    return Product.objects.create(
        name='Citrus Degreaser', description='d', directions='d', productCode='CD1', **fields)


class RecordVersionsOnSaveTests(TestCase):
    def test_a_product_without_files_gets_no_rows(self):
        make_product()
        self.assertEqual(ProductDocument.objects.count(), 0)

    def test_a_new_file_makes_one_row_per_kind(self):
        product = make_product(sdsSheet='documents/sds-v1.pdf', infoSheet='documents/info.pdf')
        kinds = sorted(ProductDocument.objects.filter(product=product).values_list('kind', flat=True))
        self.assertEqual(kinds, ['info', 'sds'])

    def test_a_second_save_makes_no_duplicate(self):
        product = make_product(sdsSheet='documents/sds-v1.pdf')
        product.name = 'Citrus Degreaser 2'
        product.save()
        self.assertEqual(ProductDocument.objects.filter(kind='sds').count(), 1)

    def test_a_changed_file_adds_a_version_and_keeps_the_old_one(self):
        product = make_product(sdsSheet='documents/sds-v1.pdf')
        product.sdsSheet = 'documents/sds-v2.pdf'
        product.save()
        rows = ProductDocument.objects.filter(product=product, kind='sds')
        self.assertEqual(rows.count(), 2)
        current = [row.file.name for row in rows if row.is_current]
        self.assertEqual(current, ['documents/sds-v2.pdf'])

    def test_mpi_approval_is_recorded(self):
        make_product(mpi_approval_sheet='documents/mpi.pdf')
        self.assertTrue(ProductDocument.objects.filter(kind='mpi_approval').exists())

    def test_a_label_is_recorded_on_its_size(self):
        product = make_product()
        variant = ProductVariant.objects.create(
            product=product, pack_size=1, code='CD5', label='documents/label-5l.pdf')
        row = ProductDocument.objects.get(kind='label')
        self.assertEqual((row.product, row.variant), (product, variant))
        self.assertTrue(row.is_current)

    def test_the_same_label_file_on_two_sizes_makes_two_rows(self):
        product = make_product()
        ProductVariant.objects.create(product=product, pack_size=1, code='CD5', label='documents/label.pdf')
        ProductVariant.objects.create(product=product, pack_size=1, code='CD20', label='documents/label.pdf')
        self.assertEqual(ProductDocument.objects.filter(kind='label').count(), 2)

    def test_str(self):
        product = make_product()
        row = ProductDocument.objects.create(product=product, kind='sds', file='documents/a.pdf', version='3')
        self.assertEqual(str(row), 'Citrus Degreaser SDS v3')


class BackfillMigrationTests(TestCase):
    def test_backfill_makes_rows_for_files_that_exist_now(self):
        product = make_product()
        variant = ProductVariant.objects.create(product=product, pack_size=1, code='CD5')
        # A queryset update sends no post_save, as before this feature.
        Product.objects.filter(pk=product.pk).update(
            sdsSheet='documents/sds.pdf', infoSheet='documents/info.pdf')
        ProductVariant.objects.filter(pk=variant.pk).update(label='documents/label.pdf')
        self.assertEqual(ProductDocument.objects.count(), 0)

        backfill_migration.backfill(apps, None)

        rows = {(row.kind, row.variant_id, row.file.name) for row in ProductDocument.objects.all()}
        self.assertEqual(rows, {
            ('sds', None, 'documents/sds.pdf'),
            ('info', None, 'documents/info.pdf'),
            ('label', variant.id, 'documents/label.pdf'),
        })
        self.assertTrue(all(row.version == '' and row.issued_on is None
                            for row in ProductDocument.objects.all()))


class DocumentSendTests(TestCase):
    def test_a_send_keeps_the_version_and_name_when_the_product_goes(self):
        product = make_product(sdsSheet='documents/sds.pdf')
        version = ProductDocument.objects.get(kind='sds')
        send = DocumentSend.objects.create(recipients=['jane@acme.test'])
        item = DocumentSendItem.objects.create(
            send=send, product=product, product_name=product.name, kind='sds', document=version)
        self.assertEqual(str(item), 'Citrus Degreaser SDS')
        self.assertIn('jane@acme.test', str(send))

        product.delete()
        item.refresh_from_db()
        self.assertIsNone(item.product)
        self.assertEqual(item.product_name, 'Citrus Degreaser')
