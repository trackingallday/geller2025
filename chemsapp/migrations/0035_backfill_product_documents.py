"""Make one ProductDocument for each document file that a product has now.

The rows have no version and no date. Staff can add them later. The file
fields on Product and ProductVariant stay the pointer to the current file.
"""

from django.db import migrations

PRODUCT_FIELDS = {
    'sds': 'sdsSheet',
    'info': 'infoSheet',
    'mpi_approval': 'mpi_approval_sheet',
}


def backfill(apps, schema_editor):
    Product = apps.get_model('chemsapp', 'Product')
    ProductVariant = apps.get_model('chemsapp', 'ProductVariant')
    ProductDocument = apps.get_model('chemsapp', 'ProductDocument')

    rows = []
    for product in Product.objects.all().only('id', *PRODUCT_FIELDS.values()):
        for kind, field in PRODUCT_FIELDS.items():
            current = getattr(product, field)
            if current and current.name:
                rows.append(ProductDocument(product_id=product.id, kind=kind, file=current.name))
    for variant in ProductVariant.objects.exclude(label='').exclude(label__isnull=True).only('id', 'product_id', 'label'):
        rows.append(ProductDocument(
            product_id=variant.product_id, variant_id=variant.id, kind='label', file=variant.label.name))
    ProductDocument.objects.bulk_create(rows, batch_size=500)


def unbackfill(apps, schema_editor):
    apps.get_model('chemsapp', 'ProductDocument').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0034_product_documents'),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
