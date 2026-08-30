"""Check the PricingVariant duplicate rule against a throwaway sqlite DB.

Run with: .venv/bin/python -m pytest <this file> -x -q
Uses an in-memory sqlite database, so the Railway production DB is never touched.
"""
from django.test import TestCase
from django.contrib.auth.models import User

from chemsapp.models import Product, Customer, PricingVariant
from chemsapp.forms import PricingVariantForm


def make_customer(username):
    user = User.objects.create(username=username, email=f'{username}@example.com')
    return Customer.objects.create(
        user=user, phoneNumber='123', businessName=f'Biz {username}', address='1 Road')


class PricingVariantRuleTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Cleaner', description='d', directions='d', productCode='C1', brand='b')
        self.other_product = Product.objects.create(
            name='Degreaser', description='d', directions='d', productCode='C2', brand='b')
        self.alice = make_customer('alice')
        self.bob = make_customer('bob')

    def form(self, product, customers, price, instance=None):
        data = {
            'product': product.pk,
            'customers': [c.pk for c in customers],
            'price': price,
            'name': '',
        }
        return PricingVariantForm(data, instance=instance)

    def test_first_variant_is_valid(self):
        form = self.form(self.product, [self.alice, self.bob], '10.50')
        self.assertTrue(form.is_valid(), form.errors)
        variant = form.save()
        self.assertEqual(variant.customers.count(), 2)
        # reverse accessors
        self.assertEqual(self.alice.pricing_variants.count(), 1)
        self.assertEqual(self.product.pricing_variants.count(), 1)

    def test_duplicate_customer_same_product_is_rejected(self):
        self.form(self.product, [self.alice, self.bob], '10.50').save()
        form = self.form(self.product, [self.alice], '9.00')
        self.assertFalse(form.is_valid())
        self.assertIn('already have a price', str(form.errors))
        self.assertIn('alice', str(form.errors))

    def test_same_customer_different_product_is_allowed(self):
        self.form(self.product, [self.alice], '10.50').save()
        form = self.form(self.other_product, [self.alice], '9.00')
        self.assertTrue(form.is_valid(), form.errors)

    def test_editing_existing_variant_does_not_clash_with_itself(self):
        variant = self.form(self.product, [self.alice], '10.50').save()
        form = self.form(self.product, [self.alice], '11.00', instance=variant)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(str(form.save().price), '11.00')

    def test_variant_with_no_customers_is_allowed(self):
        form = self.form(self.product, [], '10.50')
        self.assertTrue(form.is_valid(), form.errors)

    def test_str_uses_optional_name(self):
        variant = PricingVariant.objects.create(product=self.product, price='10.50')
        self.assertEqual(str(variant), 'Cleaner - 10.50')
        variant.name = 'Bulk tier'
        self.assertEqual(str(variant), 'Cleaner (Bulk tier) - 10.50')
