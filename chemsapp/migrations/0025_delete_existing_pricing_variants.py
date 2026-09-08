"""Clear PricingVariant before its FK changes shape.

Split out of the schema change (0026) into its own migration, so the DELETE
commits before the ALTER TABLE runs. In the same transaction, Postgres
refuses to drop a foreign key constraint on a table that still has pending
trigger events from a row deletion just done in that transaction:

    django.db.utils.OperationalError: cannot ALTER TABLE
    "chemsapp_pricingvariant" because it has pending trigger events

Existing rows point at a product with no single matching variant, so there
is no correct variant to repoint them at. The client asked to drop them and
re-enter prices per variant, rather than guess.
"""
from django.db import migrations


def delete_existing_pricing_variants(apps, schema_editor):
    PricingVariant = apps.get_model('chemsapp', 'PricingVariant')
    PricingVariant.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0024_productvariant_recommended_retail_price'),
    ]

    operations = [
        migrations.RunPython(
            delete_existing_pricing_variants, migrations.RunPython.noop),
    ]
