"""Move price from Product to ProductVariant.

Product.recommended_retail_price is removed: a product's variants each carry
their own recommended_retail_price already (migration 0024). PricingVariant
moves from a FK on Product to a FK on ProductVariant, so a negotiated price
applies to one size, not every size of a product.

Existing PricingVariant rows point at a product with no single matching
variant, so there is no correct variant to repoint them at. The client asked
to drop them and re-enter prices per variant, rather than guess.
"""
from django.db import migrations, models
import django.db.models.deletion


def delete_existing_pricing_variants(apps, schema_editor):
    PricingVariant = apps.get_model('chemsapp', 'PricingVariant')
    PricingVariant.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0024_productvariant_recommended_retail_price'),
    ]

    operations = [
        # Clear the table before the FK changes shape, while `product` still
        # exists on the model. Nothing here can pick the right variant for
        # an old product-level price, so this must run first, not as an
        # AlterField default.
        migrations.RunPython(
            delete_existing_pricing_variants, migrations.RunPython.noop),

        migrations.RemoveField(
            model_name='pricingvariant',
            name='product',
        ),
        migrations.AddField(
            model_name='pricingvariant',
            name='product_variant',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pricing_variants', to='chemsapp.productvariant',
                # The table is empty at this point, so there are no existing
                # rows for this default to satisfy — it only keeps
                # AddField from asking for one that will never be used.
                default=None, null=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pricingvariant',
            name='price',
            field=models.DecimalField(
                decimal_places=2, max_digits=10,
                help_text='Price that these customers pay for this variant, in dollars.'),
        ),
        migrations.AlterModelOptions(
            name='pricingvariant',
            options={'ordering': [
                'product_variant__product__name', 'product_variant__code', 'price']},
        ),
        migrations.RemoveField(
            model_name='product',
            name='recommended_retail_price',
        ),
    ]
