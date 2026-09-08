"""Move price from Product to ProductVariant.

Product.recommended_retail_price is removed: a product's variants each carry
their own recommended_retail_price already (migration 0024). PricingVariant
moves from a FK on Product to a FK on ProductVariant, so a negotiated price
applies to one size, not every size of a product.

The table is empty by this point — 0025 cleared it in its own transaction,
so this ALTER TABLE does not run into Postgres's "pending trigger events"
restriction.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0025_delete_existing_pricing_variants'),
    ]

    operations = [
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
