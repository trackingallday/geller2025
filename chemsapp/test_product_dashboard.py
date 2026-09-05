"""Tests for the product dashboard at /product-dashboard/."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from chemsapp.product_dashboard_views import VARIANT_SEARCH_LENGTH
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
        """A product opens on the Product tab, the first of the tabs."""
        response = self.client.get(self.url, {'product': self.product.pk})
        self.assertContains(response, 'CLEANO5')
        self.assertEqual(response.context['active_tab'], 'product')
        self.assertContains(response, 'Save details')

    def test_bad_tab_falls_back_to_the_first_tab(self):
        response = self.client.get(self.url, {'product': self.product.pk, 'tab': 'nonsense'})
        self.assertEqual(response.context['active_tab'], 'product')

    def test_the_tabs_are_in_the_order_the_client_asked_for(self):
        response = self.client.get(self.url, {'product': self.product.pk})
        self.assertEqual(
            [key for key, label in response.context['tabs']],
            ['product', 'variants', 'customers', 'compliance', 'dilutions',
             'prices', 'equivalents'])

    def test_list_query_count_is_flat(self):
        """Adding products must not add queries. This proves the prefetch works.

        Five queries: the session, the user, the products, one for every
        variant of every product together, and one for the sizes of those
        variants. The list shows the size of each variant.
        """
        with self.assertNumQueries(5):
            self.client.get(self.url)
        for i in range(20):
            make_product(f'Filler {i}', f'FILL{i}')
        with self.assertNumQueries(5):
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

    def test_save_a_variant_price(self):
        self.client.post(
            reverse('save_variants', args=[self.product.pk]),
            {
                'variants-TOTAL_FORMS': '1', 'variants-INITIAL_FORMS': '1',
                'variants-MIN_NUM_FORMS': '0', 'variants-MAX_NUM_FORMS': '1000',
                'variants-0-id': str(self.variant.pk),
                'variants-0-code': 'CLEANO5-5L', 'variants-0-size': str(self.size.pk),
                'variants-0-pack_size': '3', 'variants-0-barcode': '9421033275684',
                'variants-0-recommended_retail_price': '48.50',
                'variants-0-description': '',
            })
        self.variant.refresh_from_db()
        self.assertEqual(str(self.variant.recommended_retail_price), '48.50')

    def test_a_variant_price_can_be_left_blank(self):
        self.client.post(
            reverse('save_variants', args=[self.product.pk]),
            {
                'variants-TOTAL_FORMS': '1', 'variants-INITIAL_FORMS': '1',
                'variants-MIN_NUM_FORMS': '0', 'variants-MAX_NUM_FORMS': '1000',
                'variants-0-id': str(self.variant.pk),
                'variants-0-code': 'CLEANO5-5L', 'variants-0-size': str(self.size.pk),
                'variants-0-pack_size': '3', 'variants-0-barcode': '9421033275684',
                'variants-0-recommended_retail_price': '',
                'variants-0-description': '',
            })
        self.variant.refresh_from_db()
        self.assertIsNone(self.variant.recommended_retail_price)

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

    # --- the Customers tab ---

    def test_add_a_customer_to_the_product(self):
        customer = make_customer('linkme', 'Link Me Ltd')
        self.client.post(
            reverse('add_product_customer', args=[self.product.pk]),
            {'customer': [str(customer.pk)]})
        self.assertIn(customer, self.product.customers.all())

    def test_add_several_customers_at_once(self):
        first = make_customer('first', 'First Ltd')
        second = make_customer('second', 'Second Ltd')
        self.client.post(
            reverse('add_product_customer', args=[self.product.pk]),
            {'customer': [str(first.pk), str(second.pk)]})
        self.assertEqual(self.product.customers.count(), 2)

    def test_adding_the_same_customer_twice_makes_one_link(self):
        customer = make_customer('twice', 'Twice Ltd')
        for _ in range(2):
            self.client.post(
                reverse('add_product_customer', args=[self.product.pk]),
                {'customer': [str(customer.pk)]})
        self.assertEqual(self.product.customers.count(), 1)

    def test_adding_no_customer_reports_an_error(self):
        response = self.client.post(
            reverse('add_product_customer', args=[self.product.pk]), {}, follow=True)
        self.assertContains(response, 'Select a customer first')
        self.assertEqual(self.product.customers.count(), 0)

    def test_remove_a_customer_from_the_product(self):
        customer = make_customer('dropme', 'Drop Me Ltd')
        customer.products.add(self.product)
        self.client.post(
            reverse('remove_product_customer', args=[self.product.pk, customer.pk]))
        self.assertEqual(self.product.customers.count(), 0)

    def test_removing_a_customer_keeps_their_other_products(self):
        """Unlinking one product must not touch the customer's other products."""
        customer = make_customer('keeps', 'Keeps Ltd')
        customer.products.add(self.product, self.other)
        self.client.post(
            reverse('remove_product_customer', args=[self.product.pk, customer.pk]))
        self.assertEqual(list(customer.products.all()), [self.other])

    def test_customer_search_can_hide_customers_already_linked(self):
        linked = make_customer('linked', 'Linked Ltd')
        make_customer('unlinked', 'Unlinked Ltd')
        linked.products.add(self.product)

        response = self.client.get(
            reverse('dashboard_customer_search'), {'exclude_linked': self.product.pk})
        names = [row['name'] for row in response.json()['results']]
        self.assertIn('Unlinked Ltd', names)
        self.assertNotIn('Linked Ltd', names)

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
            reverse('dashboard_customer_search'), {'exclude_priced': self.product.pk})
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


class VariantFocusTests(TestCase):
    """The variant-focused dashboard: search, focus pane and per-variant save.

    The client works in variants, not products. A search must reach a
    variant, and a click on one must open it in the focus pane.
    """

    def setUp(self):
        User.objects.create_user('staffer', password='pw12345678', is_staff=True)
        self.client.login(username='staffer', password='pw12345678')
        self.url = reverse('product_dashboard')
        self.product = make_product('Clean Green HD', 'CLEANO5')
        self.other_product = make_product('Lemon Dishwash', 'DISH01', brand='Kemsol')
        self.size_5l = Size.objects.create(
            name='5L', desc='5 litre', amount='5', volume_litres='5.000')
        self.size_20l = Size.objects.create(
            name='20L', desc='20 litre', amount='20', volume_litres='20.000')
        self.variant = ProductVariant.objects.create(
            product=self.product, size=self.size_5l, pack_size=3,
            barcode='9421033275684', code='CLEANO5-5L')
        self.second = ProductVariant.objects.create(
            product=self.product, size=self.size_20l, pack_size=1,
            barcode='9421033275691', code='CLEANO5-20L')
        self.foreign = ProductVariant.objects.create(
            product=self.other_product, size=self.size_5l, pack_size=6,
            barcode='9421033275707', code='DISH01-5L')

    # --- the left list ---

    def test_search_matches_a_variant_code(self):
        response = self.client.get(self.url, {'q': 'CLEANO5-20L'})
        self.assertContains(response, 'Clean Green HD')
        self.assertContains(response, 'CLEANO5-20L')
        self.assertNotContains(response, 'DISH01-5L')

    def test_search_matches_a_variant_barcode(self):
        response = self.client.get(self.url, {'q': '9421033275691'})
        self.assertContains(response, 'CLEANO5-20L')

    def test_search_matches_a_variant_size(self):
        """A search for the size name reaches every variant of that size."""
        Size.objects.filter(pk=self.size_20l.pk).update(name='20 Litre')
        response = self.client.get(self.url, {'q': '20 Litre'})
        self.assertContains(response, 'CLEANO5-20L')
        self.assertNotContains(response, 'DISH01-5L')

    def test_a_variant_match_shows_a_product_that_does_not_match(self):
        """The product row is the group header, even when it does not match."""
        response = self.client.get(self.url, {'q': '9421033275707'})
        self.assertContains(response, 'Lemon Dishwash')
        self.assertNotContains(response, 'Clean Green HD')

    def test_a_product_match_shows_its_variants(self):
        """A product in the results lists its variants, so one is one click away."""
        response = self.client.get(self.url, {'q': 'Kemsol'})
        self.assertContains(response, 'Lemon Dishwash')
        self.assertContains(response, 'DISH01-5L')

    def test_a_short_search_shows_no_variant_rows(self):
        """The first few characters match too many products to nest variants."""
        response = self.client.get(self.url, {'q': 'Kem'})
        self.assertContains(response, 'Lemon Dishwash')
        self.assertNotContains(response, 'DISH01-5L')

    def test_the_length_limit_is_the_constant(self):
        """A term of exactly VARIANT_SEARCH_LENGTH characters shows variants."""
        term = 'CLEA'
        self.assertEqual(len(term), VARIANT_SEARCH_LENGTH)
        response = self.client.get(self.url, {'q': term})
        self.assertContains(response, 'CLEANO5-5L')
        short = self.client.get(self.url, {'q': term[:-1]})
        self.assertNotContains(short, 'CLEANO5-5L')

    def test_an_empty_search_shows_no_variant_rows(self):
        rows = self.client.get(self.url).context['product_rows']
        self.assertEqual([row['variants'] for row in rows], [[], []])

    def test_search_query_count_is_flat(self):
        """More products must not add queries to the grouped search."""
        def count():
            self.client.get(self.url, {'q': 'CLEANO5'})

        with self.assertNumQueries(6):
            count()
        for i in range(10):
            product = make_product(f'Filler {i}', f'CLEANO5-FILL{i}')
            ProductVariant.objects.create(
                product=product, size=self.size_5l, pack_size=1,
                barcode=f'barcode{i}', code=f'FILL{i}-5L')
        with self.assertNumQueries(6):
            count()

    # --- the live search endpoint ---

    def test_product_list_returns_the_rows(self):
        """The search box asks for HTML rows, not a whole page."""
        response = self.client.get(
            reverse('dashboard_product_list'), {'q': 'CLEANO5-20L'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CLEANO5-20L')
        self.assertContains(response, 'Clean Green HD')
        # A fragment, not a page.
        self.assertNotContains(response, '<html')

    def test_product_list_nests_variants_under_the_product(self):
        """The product row comes first, then its variant rows."""
        response = self.client.get(
            reverse('dashboard_product_list'), {'q': 'Clean Green'})
        body = response.content.decode()
        self.assertLess(
            body.index('product-list-item'), body.index('variant-list-item'),
            'the product row must come before its variant rows')
        self.assertIn('CLEANO5-5L', body)

    def test_product_list_with_no_search_lists_every_product(self):
        response = self.client.get(reverse('dashboard_product_list'))
        self.assertContains(response, 'Clean Green HD')
        self.assertContains(response, 'Lemon Dishwash')
        self.assertNotContains(response, 'variant-list-item')

    def test_product_list_reports_no_match(self):
        response = self.client.get(
            reverse('dashboard_product_list'), {'q': 'nothing matches this'})
        self.assertContains(response, 'Nothing matches')

    def test_product_list_marks_the_open_variant(self):
        """The row of the variant in the focus pane keeps its mark."""
        response = self.client.get(reverse('dashboard_product_list'), {
            'q': 'CLEANO5', 'product': str(self.product.pk),
            'tab': 'variants', 'variant': str(self.second.pk)})
        body = response.content.decode()
        marked = body.index(f'data-variant="{self.second.pk}"')
        self.assertIn('active', body[marked:marked + 120])

    def test_product_list_needs_staff(self):
        self.client.logout()
        response = self.client.get(reverse('dashboard_product_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    # --- the focus pane ---

    def test_variant_id_focuses_that_variant(self):
        response = self.client.get(
            self.url,
            {'product': self.product.pk, 'tab': 'variants', 'variant': self.second.pk})
        self.assertEqual(response.context['focus_variant'], self.second)
        self.assertEqual(response.context['other_variants'], [self.variant])

    def test_no_variant_id_focuses_the_first_variant(self):
        response = self.client.get(
            self.url, {'product': self.product.pk, 'tab': 'variants'})
        self.assertEqual(response.context['focus_variant'], self.variant)

    def test_a_variant_of_another_product_is_ignored(self):
        """A stray id must not show one product's variant under another."""
        response = self.client.get(
            self.url,
            {'product': self.product.pk, 'tab': 'variants', 'variant': self.foreign.pk})
        self.assertEqual(response.context['focus_variant'], self.variant)

    def test_an_unknown_variant_id_does_not_break_the_page(self):
        response = self.client.get(
            self.url,
            {'product': self.product.pk, 'tab': 'variants', 'variant': '999999'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['focus_variant'], self.variant)

    def test_a_product_with_no_variant_has_no_focus(self):
        response = self.client.get(
            self.url, {'product': self.other_product.pk, 'tab': 'variants'})
        self.assertEqual(response.context['focus_variant'], self.foreign)
        self.assertEqual(response.context['other_variants'], [])

    def test_new_opens_an_empty_pane(self):
        response = self.client.get(
            self.url, {'product': self.product.pk, 'tab': 'variants', 'new': '1'})
        self.assertTrue(response.context['is_new_variant'])
        self.assertIsNone(response.context['focus_variant'])
        # With no variant in focus, every variant is an "other" variant.
        self.assertEqual(len(response.context['other_variants']), 2)

    # --- saving one variant ---

    def test_save_one_variant_returns_json(self):
        response = self.client.post(
            reverse('save_one_variant', args=[self.variant.pk]),
            {'code': 'CLEANO5-5L', 'size': str(self.size_5l.pk), 'pack_size': '4',
             'barcode': '9421033275684', 'recommended_retail_price': '24.50',
             'carton_barcode': '', 'label_code': '', 'description': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['variant']['price'], '24.50')
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.pack_size, 4)

    def test_save_one_variant_reports_an_error(self):
        """A code that another variant already uses must not save."""
        response = self.client.post(
            reverse('save_one_variant', args=[self.variant.pk]),
            {'code': 'CLEANO5-20L', 'size': str(self.size_5l.pk), 'pack_size': '3',
             'barcode': '9421033275684', 'carton_barcode': '', 'label_code': '',
             'description': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertFalse(body['ok'])
        self.assertIn('code', body['errors'])
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.code, 'CLEANO5-5L')

    def test_save_one_variant_keeps_its_product(self):
        """The save must not move the variant to another product."""
        self.client.post(
            reverse('save_one_variant', args=[self.variant.pk]),
            {'code': 'CLEANO5-5L', 'size': str(self.size_5l.pk), 'pack_size': '3',
             'barcode': '9421033275684', 'carton_barcode': '', 'label_code': '',
             'description': ''})
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.product, self.product)

    def test_create_a_variant(self):
        response = self.client.post(
            reverse('create_variant', args=[self.product.pk]),
            {'code': 'CLEANO5-1L', 'size': str(self.size_5l.pk), 'pack_size': '12',
             'barcode': '9421033275714', 'carton_barcode': '', 'label_code': '',
             'description': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(self.product.variants.count(), 3)

    def test_delete_a_variant(self):
        self.client.post(reverse('delete_variant', args=[self.second.pk]))
        self.assertEqual(self.product.variants.count(), 1)

    def test_a_form_post_with_no_javascript_redirects(self):
        """With no JavaScript the browser must get the page, not raw JSON."""
        response = self.client.post(
            reverse('save_one_variant', args=[self.variant.pk]),
            {'code': 'CLEANO5-5L', 'size': str(self.size_5l.pk), 'pack_size': '7',
             'barcode': '9421033275684', 'carton_barcode': '', 'label_code': '',
             'description': ''})
        self.assertEqual(response.status_code, 302)
        self.assertIn('tab=variants', response['Location'])
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.pack_size, 7)

    def test_a_bad_form_post_with_no_javascript_redirects(self):
        response = self.client.post(
            reverse('save_one_variant', args=[self.variant.pk]),
            {'code': 'CLEANO5-20L', 'size': str(self.size_5l.pk), 'pack_size': '3',
             'barcode': '9421033275684', 'carton_barcode': '', 'label_code': '',
             'description': ''}, follow=True)
        self.assertContains(response, 'The variant did not save')
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.code, 'CLEANO5-5L')

    def test_get_on_a_variant_save_changes_nothing(self):
        response = self.client.get(reverse('save_one_variant', args=[self.variant.pk]))
        self.assertEqual(response.status_code, 302)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.pack_size, 3)

    def test_the_variant_views_need_staff(self):
        self.client.logout()
        for name, args in [('save_one_variant', [self.variant.pk]),
                           ('create_variant', [self.product.pk]),
                           ('delete_variant', [self.variant.pk])]:
            response = self.client.post(reverse(name, args=args))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn('/admin/login/', response['Location'], name)
