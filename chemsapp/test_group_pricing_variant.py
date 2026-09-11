"""Check the GroupPricingVariant duplicate rule: the form and the database.

Run with: .venv/bin/python manage.py test chemsapp.test_group_pricing_variant
"""
from django.db import IntegrityError, transaction
from django.test import TestCase

from chemsapp.models import (
    CustomerGroup, GroupPricingVariant, Product, ProductVariant,
)
from chemsapp.forms import GroupPricingVariantForm


def make_variant(product, code, barcode):
    return ProductVariant.objects.create(
        product=product, pack_size=1, code=code, barcode=barcode)


class GroupPricingVariantRuleTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Cleaner', description='d', directions='d', productCode='C1', brand='b')
        self.variant = make_variant(self.product, 'C1-5L', '1000000000001')
        self.sibling = make_variant(self.product, 'C1-20L', '1000000000002')
        self.north = CustomerGroup.objects.create(name='North')
        self.south = CustomerGroup.objects.create(name='South')

    def form(self, product_variant, customer_group, price, instance=None):
        data = {
            'product_variant': product_variant.pk,
            'customer_group': customer_group.pk,
            'price': price,
            'name': '',
        }
        return GroupPricingVariantForm(data, instance=instance)

    def test_first_group_price_is_valid(self):
        form = self.form(self.variant, self.north, '10.50')
        self.assertTrue(form.is_valid(), form.errors)
        group_price = form.save()
        self.assertEqual(self.north.pricing_variants.count(), 1)
        self.assertEqual(self.variant.group_pricing_variants.count(), 1)
        self.assertEqual(str(group_price.price), '10.50')

    def test_second_price_for_the_same_group_and_variant_is_rejected(self):
        self.form(self.variant, self.north, '10.50').save()
        form = self.form(self.variant, self.north, '9.00')
        self.assertFalse(form.is_valid())
        self.assertIn('already has a price', str(form.errors))
        self.assertIn('North', str(form.errors))

    def test_another_group_for_the_same_variant_is_allowed(self):
        self.form(self.variant, self.north, '10.50').save()
        form = self.form(self.variant, self.south, '9.00')
        self.assertTrue(form.is_valid(), form.errors)

    def test_the_same_group_on_a_sibling_variant_is_allowed(self):
        self.form(self.variant, self.north, '10.50').save()
        form = self.form(self.sibling, self.north, '9.00')
        self.assertTrue(form.is_valid(), form.errors)

    def test_editing_an_existing_group_price_does_not_clash_with_itself(self):
        group_price = self.form(self.variant, self.north, '10.50').save()
        form = self.form(self.variant, self.north, '11.00', instance=group_price)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(str(form.save().price), '11.00')

    def test_the_database_constraint_blocks_a_raw_duplicate(self):
        GroupPricingVariant.objects.create(
            product_variant=self.variant, customer_group=self.north, price='10.50')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GroupPricingVariant.objects.create(
                    product_variant=self.variant, customer_group=self.north, price='9.00')

    def test_str_uses_the_optional_name(self):
        group_price = GroupPricingVariant.objects.create(
            product_variant=self.variant, customer_group=self.north, price='10.50')
        self.assertIn('North', str(group_price))
        self.assertIn('10.50', str(group_price))
        group_price.name = 'Bulk tier'
        self.assertIn('(Bulk tier)', str(group_price))
