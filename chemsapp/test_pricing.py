"""Tests for chemsapp.pricing.resolve_price."""
from django.contrib.auth.models import User
from django.test import TestCase

from chemsapp.models import (
    Customer, CustomerGroup, GroupPricingVariant, PricingVariant, Product,
    ProductVariant,
)
from chemsapp.pricing import resolve_price


def make_customer(username, business, group=None):
    user = User.objects.create(username=username, email=f'{username}@example.com')
    return Customer.objects.create(
        user=user, phoneNumber='123', businessName=business, address='1 Road',
        group=group)


class ResolvePriceTests(TestCase):
    def setUp(self):
        product = Product.objects.create(
            name='Cleaner', description='d', directions='d', productCode='C1', brand='b')
        self.variant = ProductVariant.objects.create(
            product=product, pack_size=1, code='C1-5L', barcode='1',
            recommended_retail_price='100.00')
        self.no_rrp_variant = ProductVariant.objects.create(
            product=product, pack_size=1, code='C1-20L', barcode='2')
        self.alice = make_customer('alice', 'Alice Ltd')
        self.bob = make_customer('bob', 'Bob Ltd')

    def test_a_customer_with_a_price_pays_that_price(self):
        pricing = PricingVariant.objects.create(
            product_variant=self.variant, price='80.00')
        pricing.customers.add(self.alice)

        price, source = resolve_price(self.variant, self.alice)
        self.assertEqual(str(price), '80.00')
        self.assertEqual(source, pricing)

    def test_a_customer_with_no_price_pays_the_variant_rrp(self):
        price, source = resolve_price(self.variant, self.bob)
        self.assertEqual(str(price), '100.00')
        self.assertIsNone(source)

    def test_with_no_customer_the_rrp_applies(self):
        price, source = resolve_price(self.variant, None)
        self.assertEqual(str(price), '100.00')
        self.assertIsNone(source)

    def test_a_customer_price_on_one_variant_does_not_reach_another(self):
        """A price is per (variant, customer). A sibling variant of the same
        product falls back to its own RRP, or to nothing if it has none."""
        pricing = PricingVariant.objects.create(
            product_variant=self.variant, price='80.00')
        pricing.customers.add(self.alice)

        price, source = resolve_price(self.no_rrp_variant, self.alice)
        self.assertIsNone(price)
        self.assertIsNone(source)

    def test_no_price_and_no_rrp_resolves_to_none(self):
        price, source = resolve_price(self.no_rrp_variant, self.bob)
        self.assertIsNone(price)
        self.assertIsNone(source)

    def test_a_none_variant_resolves_to_none(self):
        price, source = resolve_price(None, self.alice)
        self.assertIsNone(price)
        self.assertIsNone(source)


class ResolvePriceGroupTests(TestCase):
    """The middle level of the chain: RRP -> group price -> customer price."""

    def setUp(self):
        product = Product.objects.create(
            name='Cleaner', description='d', directions='d', productCode='C1', brand='b')
        self.variant = ProductVariant.objects.create(
            product=product, pack_size=1, code='C1-5L', barcode='1',
            recommended_retail_price='100.00')
        self.sibling = ProductVariant.objects.create(
            product=product, pack_size=1, code='C1-20L', barcode='2',
            recommended_retail_price='300.00')
        self.north = CustomerGroup.objects.create(name='North')
        self.south = CustomerGroup.objects.create(name='South')
        self.grouped = make_customer('grouped', 'Grouped Ltd', group=self.north)
        self.ungrouped = make_customer('ungrouped', 'Ungrouped Ltd')

    def test_a_grouped_customer_with_no_customer_price_gets_the_group_price(self):
        group_price = GroupPricingVariant.objects.create(
            product_variant=self.variant, customer_group=self.north, price='70.00')

        price, source = resolve_price(self.variant, self.grouped)
        self.assertEqual(str(price), '70.00')
        self.assertEqual(source, group_price)

    def test_a_customer_price_wins_over_the_group_price(self):
        GroupPricingVariant.objects.create(
            product_variant=self.variant, customer_group=self.north, price='70.00')
        customer_price = PricingVariant.objects.create(
            product_variant=self.variant, price='50.00')
        customer_price.customers.add(self.grouped)

        price, source = resolve_price(self.variant, self.grouped)
        self.assertEqual(str(price), '50.00')
        self.assertEqual(source, customer_price)

    def test_the_group_price_wins_over_the_rrp(self):
        GroupPricingVariant.objects.create(
            product_variant=self.variant, customer_group=self.north, price='70.00')

        price, source = resolve_price(self.variant, self.grouped)
        self.assertEqual(str(price), '70.00')

    def test_a_customer_with_no_group_and_no_price_gets_the_rrp(self):
        GroupPricingVariant.objects.create(
            product_variant=self.variant, customer_group=self.north, price='70.00')

        price, source = resolve_price(self.variant, self.ungrouped)
        self.assertEqual(str(price), '100.00')
        self.assertIsNone(source)

    def test_a_group_price_for_another_group_does_not_apply(self):
        GroupPricingVariant.objects.create(
            product_variant=self.variant, customer_group=self.south, price='70.00')

        price, source = resolve_price(self.variant, self.grouped)
        self.assertEqual(str(price), '100.00')
        self.assertIsNone(source)

    def test_a_group_price_on_one_variant_does_not_reach_a_sibling(self):
        GroupPricingVariant.objects.create(
            product_variant=self.variant, customer_group=self.north, price='70.00')

        price, source = resolve_price(self.sibling, self.grouped)
        self.assertEqual(str(price), '300.00')
        self.assertIsNone(source)
