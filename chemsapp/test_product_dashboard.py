"""Tests for the product dashboard at /product-dashboard/."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from chemsapp.models import (
    ApplicationType, Customer, DilutionVariant, PricingVariant, Product,
    ProductCategory, ProductEquivalency, ProductVariant, SafetyWear, Size,
)


def make_product(name, code, brand='Geller'):
    return Product.objects.create(
        name=name, description='d', directions='d', productCode=code, brand=brand)


def make_customer(username, business):
    user = User.objects.create(username=username, email=f'{username}@example.com')
    return Customer.objects.create(
        user=user, phoneNumber='123', businessName=business, address='1 Road')


class ProductDashboardAccessTests(TestCase):
    def setUp(self):
        self.url = reverse('product_dashboard')

    def test_signed_out_user_is_sent_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_non_staff_user_is_refused(self):
        User.objects.create_user('plain', password='pw12345678')
        self.client.login(username='plain', password='pw12345678')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_staff_user_can_open_the_page(self):
        User.objects.create_user('staffer', password='pw12345678', is_staff=True)
        self.client.login(username='staffer', password='pw12345678')
        self.assertEqual(self.client.get(self.url).status_code, 200)


class ProductDashboardTests(TestCase):
    def setUp(self):
        User.objects.create_user('staffer', password='pw12345678', is_staff=True)
        self.client.login(username='staffer', password='pw12345678')
        self.url = reverse('product_dashboard')
        self.product = make_product('Clean Green HD', 'CLEANO5')
        self.other = make_product('Lemon Dishwash', 'DISH01', brand='Kemsol')
        self.size = Size.objects.create(
            name='5L', desc='5 litre', amount='5', volume_litres='5.000')
        self.variant = ProductVariant.objects.create(
            product=self.product, size=self.size, pack_size=3, barcode='9421033275684',
            code='CLEANO5-5L')

    def test_list_shows_products(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Clean Green HD')
        self.assertContains(response, 'Lemon Dishwash')

    def test_search_filters_the_list(self):
        response = self.client.get(self.url, {'q': 'Lemon'})
        self.assertContains(response, 'Lemon Dishwash')
        self.assertNotContains(response, 'Clean Green HD')

    def test_search_matches_code_and_brand(self):
        self.assertContains(self.client.get(self.url, {'q': 'CLEANO5'}), 'Clean Green HD')
        self.assertContains(self.client.get(self.url, {'q': 'Kemsol'}), 'Lemon Dishwash')

    def test_unknown_product_id_does_not_break_the_page(self):
        response = self.client.get(self.url, {'product': '999999'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select a product')

    def test_selecting_a_product_shows_the_editor(self):
        response = self.client.get(self.url, {'product': self.product.pk})
        self.assertContains(response, 'CLEANO5')
        self.assertContains(response, 'Recommended retail price')

    def test_bad_tab_falls_back_to_prices(self):
        response = self.client.get(self.url, {'product': self.product.pk, 'tab': 'nonsense'})
        self.assertEqual(response.context['active_tab'], 'prices')

    def test_list_query_count_is_flat(self):
        """Adding products must not add queries. This proves the prefetch works.

        Four queries: the session, the user, the products, and one more for
        every variant of every product together.
        """
        with self.assertNumQueries(4):
            self.client.get(self.url)
        for i in range(20):
            make_product(f'Filler {i}', f'FILL{i}')
        with self.assertNumQueries(4):
            self.client.get(self.url)

    # --- saving ---

    def test_save_rrp(self):
        self.client.post(
            reverse('save_product_rrp', args=[self.product.pk]),
            {'recommended_retail_price': '24.60'})
        self.product.refresh_from_db()
        self.assertEqual(str(self.product.recommended_retail_price), '24.60')

    def test_save_details(self):
        self.client.post(
            reverse('save_product_details', args=[self.product.pk]),
            {'name': 'Clean Green HD', 'brand': 'Geller', 'subheading': 'Heavy duty',
             'description': 'd', 'directions': 'd', 'properties': ''})
        self.product.refresh_from_db()
        self.assertEqual(self.product.subheading, 'Heavy duty')

    def test_add_a_variant(self):
        response = self.client.post(
            reverse('save_variants', args=[self.product.pk]),
            {
                'variants-TOTAL_FORMS': '2', 'variants-INITIAL_FORMS': '1',
                'variants-MIN_NUM_FORMS': '0', 'variants-MAX_NUM_FORMS': '1000',
                'variants-0-id': str(self.variant.pk),
                'variants-0-code': 'CLEANO5-5L', 'variants-0-size': str(self.size.pk),
                'variants-0-pack_size': '3', 'variants-0-barcode': '9421033275684',
                'variants-0-description': '',
                'variants-1-code': 'CLEANO5-20L', 'variants-1-size': str(self.size.pk),
                'variants-1-pack_size': '1', 'variants-1-barcode': '9421033272331',
                'variants-1-description': '',
            })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.product.variants.count(), 2)

    def test_remove_a_variant(self):
        self.client.post(
            reverse('save_variants', args=[self.product.pk]),
            {
                'variants-TOTAL_FORMS': '1', 'variants-INITIAL_FORMS': '1',
                'variants-MIN_NUM_FORMS': '0', 'variants-MAX_NUM_FORMS': '1000',
                'variants-0-id': str(self.variant.pk),
                'variants-0-code': 'CLEANO5-5L', 'variants-0-size': str(self.size.pk),
                'variants-0-pack_size': '3', 'variants-0-barcode': '9421033275684',
                'variants-0-description': '', 'variants-0-DELETE': 'on',
            })
        self.assertEqual(self.product.variants.count(), 0)

    def test_add_a_dilution(self):
        app_type = ApplicationType.objects.create(
            name='Spray Bottle', unit_label='per 750ml spray bottle',
            unit_volume_litres='0.750')
        prefix = f'dilution-{self.variant.pk}'
        self.client.post(
            reverse('save_dilutions', args=[self.variant.pk]),
            {
                f'{prefix}-TOTAL_FORMS': '1', f'{prefix}-INITIAL_FORMS': '0',
                f'{prefix}-MIN_NUM_FORMS': '0', f'{prefix}-MAX_NUM_FORMS': '1000',
                f'{prefix}-0-application_type': str(app_type.pk),
                f'{prefix}-0-value': '10', f'{prefix}-0-note': '',
            })
        self.assertEqual(DilutionVariant.objects.filter(variant=self.variant).count(), 1)

    # --- prices ---

    def test_add_a_pricing_variant(self):
        customer = make_customer('jimmys', 'Jimmys Pies Ltd')
        self.client.post(
            reverse('save_pricing_variant', args=[self.product.pk]),
            {'product': str(self.product.pk), 'price': '22.38',
             'name': 'Sell Price 1', 'customers': [str(customer.pk)]})
        pricing = PricingVariant.objects.get(product=self.product)
        self.assertEqual(str(pricing.price), '22.38')
        self.assertIn(customer, pricing.customers.all())

    def test_duplicate_customer_price_is_refused(self):
        customer = make_customer('otago', 'Otago Cleaning Products')
        pricing = PricingVariant.objects.create(product=self.product, price='18.20')
        pricing.customers.add(customer)

        response = self.client.post(
            reverse('save_pricing_variant', args=[self.product.pk]),
            {'product': str(self.product.pk), 'price': '9.99',
             'name': 'Cheaper', 'customers': [str(customer.pk)]}, follow=True)

        self.assertEqual(PricingVariant.objects.filter(product=self.product).count(), 1)
        self.assertContains(response, 'already have a price')

    def test_delete_a_pricing_variant(self):
        pricing = PricingVariant.objects.create(product=self.product, price='18.20')
        self.client.post(reverse('delete_pricing_variant', args=[pricing.pk]))
        self.assertEqual(PricingVariant.objects.filter(pk=pricing.pk).count(), 0)

    # --- the fields added from the client's spreadsheet ---

    def test_save_the_new_product_fields(self):
        self.client.post(
            reverse('save_product_details', args=[self.product.pk]),
            {'name': 'Clean Green HD', 'brand': 'Geller', 'product_range': 'Professional',
             'subheading': '', 'description': 'd', 'directions': 'd', 'properties': '',
             'bom': '5L drum, cap, label'})
        self.product.refresh_from_db()
        self.assertEqual(self.product.product_range, 'Professional')
        self.assertEqual(self.product.bom, '5L drum, cap, label')

    def test_save_the_mpi_approval_number(self):
        self.client.post(
            reverse('save_product_compliance', args=[self.product.pk]),
            {'mpi_approval': 'C32', 'application': '', 'procedure': ''})
        self.product.refresh_from_db()
        self.assertEqual(self.product.mpi_approval, 'C32')

    def test_save_the_new_variant_fields(self):
        self.client.post(
            reverse('save_variants', args=[self.product.pk]),
            {
                'variants-TOTAL_FORMS': '1', 'variants-INITIAL_FORMS': '1',
                'variants-MIN_NUM_FORMS': '0', 'variants-MAX_NUM_FORMS': '1000',
                'variants-0-id': str(self.variant.pk),
                'variants-0-code': 'CLEANO5-5L', 'variants-0-size': str(self.size.pk),
                'variants-0-pack_size': '3', 'variants-0-barcode': '9421033275684',
                'variants-0-carton_barcode': '9421033272331',
                'variants-0-label_code': 'LABCLEANG05', 'variants-0-description': '',
            })
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.carton_barcode, '9421033272331')
        self.assertEqual(self.variant.label_code, 'LABCLEANG05')

    def test_price_records_a_minimum_quantity(self):
        customer = make_customer('jimmys2', 'Jimmys Pies Ltd')
        self.client.post(
            reverse('save_pricing_variant', args=[self.product.pk]),
            {'product': str(self.product.pk), 'price': '22.38', 'name': 'Bulk',
             'min_quantity': '144', 'customers': [str(customer.pk)]})
        self.assertEqual(PricingVariant.objects.get(product=self.product).min_quantity, 144)

    def test_add_an_equivalent_product(self):
        self.client.post(
            reverse('save_equivalents', args=[self.product.pk]),
            {
                'equivalents-TOTAL_FORMS': '1', 'equivalents-INITIAL_FORMS': '0',
                'equivalents-MIN_NUM_FORMS': '0', 'equivalents-MAX_NUM_FORMS': '1000',
                'equivalents-0-equivalent_product': str(self.other.pk),
                'equivalents-0-note': 'Same dilution',
            })
        equivalency = ProductEquivalency.objects.get(product=self.product)
        self.assertEqual(equivalency.equivalent_product, self.other)
        self.assertEqual(equivalency.note, 'Same dilution')

    def test_a_product_cannot_be_equivalent_to_itself(self):
        self.client.post(
            reverse('save_equivalents', args=[self.product.pk]),
            {
                'equivalents-TOTAL_FORMS': '1', 'equivalents-INITIAL_FORMS': '0',
                'equivalents-MIN_NUM_FORMS': '0', 'equivalents-MAX_NUM_FORMS': '1000',
                'equivalents-0-equivalent_product': str(self.product.pk),
                'equivalents-0-note': '',
            })
        self.assertEqual(ProductEquivalency.objects.count(), 0)

    def test_the_same_equivalent_cannot_be_added_twice(self):
        ProductEquivalency.objects.create(
            product=self.product, equivalent_product=self.other)
        self.client.post(
            reverse('save_equivalents', args=[self.product.pk]),
            {
                'equivalents-TOTAL_FORMS': '1', 'equivalents-INITIAL_FORMS': '0',
                'equivalents-MIN_NUM_FORMS': '0', 'equivalents-MAX_NUM_FORMS': '1000',
                'equivalents-0-equivalent_product': str(self.other.pk),
                'equivalents-0-note': '',
            })
        self.assertEqual(ProductEquivalency.objects.count(), 1)

    # --- the search-and-add pickers ---

    def test_customer_search_matches_business_name(self):
        make_customer('jimmys3', 'Jimmys Pies Ltd')
        make_customer('otago3', 'Otago Cleaning')
        response = self.client.get(reverse('dashboard_customer_search'), {'q': 'Jimmy'})
        names = [row['name'] for row in response.json()['results']]
        self.assertIn('Jimmys Pies Ltd', names)
        self.assertNotIn('Otago Cleaning', names)

    def test_customer_search_hides_customers_that_already_have_a_price(self):
        taken = make_customer('taken', 'Taken Ltd')
        free = make_customer('free', 'Free Ltd')
        pricing = PricingVariant.objects.create(product=self.product, price='10.00')
        pricing.customers.add(taken)

        response = self.client.get(
            reverse('dashboard_customer_search'), {'product': self.product.pk})
        names = [row['name'] for row in response.json()['results']]
        self.assertIn('Free Ltd', names)
        self.assertNotIn('Taken Ltd', names)

    def test_category_search_filters_by_name(self):
        ProductCategory.objects.create(name='Kitchen')
        ProductCategory.objects.create(name='Laundry')
        response = self.client.get(reverse('dashboard_category_search'), {'q': 'Kitch'})
        names = [row['name'] for row in response.json()['results']]
        self.assertEqual(names, ['Kitchen'])

    def test_category_search_returns_every_category_when_nothing_is_typed(self):
        """The category list is short, so staff can browse it without typing."""
        for i in range(60):
            ProductCategory.objects.create(name=f'Category {i:02d}')
        response = self.client.get(reverse('dashboard_category_search'))
        results = response.json()['results']
        self.assertEqual(len(results), 60)
        self.assertEqual(results[0]['name'], 'Category 00')

    def test_customer_search_stays_capped(self):
        """Customers grow without limit, so that list keeps its cap."""
        for i in range(60):
            make_customer(f'bulk{i}', f'Bulk Customer {i:02d}')
        response = self.client.get(reverse('dashboard_customer_search'))
        self.assertEqual(len(response.json()['results']), 50)

    def test_search_endpoints_need_staff(self):
        self.client.logout()
        for name in ['dashboard_customer_search', 'dashboard_category_search']:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)

    def test_categories_posted_as_repeated_values_are_saved(self):
        """The picker posts one input for each choice, like a multi-select."""
        kitchen = ProductCategory.objects.create(name='Kitchen')
        laundry = ProductCategory.objects.create(name='Laundry')
        self.client.post(
            reverse('save_product_details', args=[self.product.pk]),
            {'name': 'Clean Green HD', 'brand': 'Geller', 'description': 'd',
             'directions': 'd', 'productCategory': [str(kitchen.pk), str(laundry.pk)]})
        self.assertEqual(self.product.productCategory.count(), 2)

    def test_safety_wear_checkboxes_are_saved(self):
        gloves = SafetyWear.objects.create(name='Gloves')
        SafetyWear.objects.create(name='Boots')
        self.client.post(
            reverse('save_product_details', args=[self.product.pk]),
            {'name': 'Clean Green HD', 'brand': 'Geller', 'description': 'd',
             'directions': 'd', 'safetyWears': [str(gloves.pk)]})
        self.assertEqual(
            list(self.product.safetyWears.values_list('name', flat=True)), ['Gloves'])

    def test_get_on_a_save_view_changes_nothing(self):
        """A stray GET must not save. It just returns to the tab."""
        response = self.client.get(reverse('save_product_rrp', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertIsNone(self.product.recommended_retail_price)
