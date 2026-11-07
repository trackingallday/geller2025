"""Search on the staff lists must find a record by any word that names it."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from orders.models import CustomerOrder, OrderLineItem
from quotes.models import Quote, QuoteLine
from reports.models import Report, ReportType
from tickets.models import Ticket, TicketReply

from .models import (
    Customer, CustomerContact, CustomerGroup, Distributor, Product,
    ProductVariant,
)
from .staff_api import search_q


class SearchQTests(TestCase):
    def test_every_word_must_match_but_in_any_field_and_order(self):
        user = User.objects.create_user('jsmith', first_name='Jane', last_name='Smith')
        User.objects.create_user('other', first_name='Jane', last_name='Brown')
        fields = ('first_name', 'last_name')
        found = User.objects.filter(search_q('smith jane', fields))
        self.assertEqual(list(found), [user])

    def test_empty_search_finds_everything(self):
        User.objects.create_user('someone')
        self.assertEqual(User.objects.filter(search_q('   ', ('username',))).count(), 1)


class StaffListSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(
            'searcher', first_name='Sam', last_name='Staff', is_staff=True)
        cls.token = Token.objects.get_or_create(user=cls.staff)[0].key

        cls.group = CustomerGroup.objects.create(name='Wharf Bars', note='South Island venues')
        owner = User.objects.create_user(
            'kiwi-owner', first_name='Kim', last_name='Tane', email='kim@kiwicafe.test')
        cls.customer = Customer.objects.create(
            user=owner, businessName='Kiwi Cafe', phoneNumber='021555',
            address='1 Quay Street', group=cls.group)
        CustomerContact.objects.create(
            customer=cls.customer, name='Dana Hill', email='dana@kiwicafe.test',
            phone='0279999', role='Manager')
        other = User.objects.create_user('other-owner')
        cls.other = Customer.objects.create(
            user=other, businessName='Other Ltd', phoneNumber='1', address='x')

        cls.distributor = Distributor.objects.create(
            businessname='Southern Supplies', phonenumber='034444', address='Depot Road')
        cls.distributor.customers.add(cls.customer)
        cls.distributor.users.add(owner)

        cls.product = Product.objects.create(
            name='Citrus Degreaser', productCode='CD1', brand='Geller',
            subheading='For kitchens', product_range='Foodsafe')
        cls.variant = ProductVariant.objects.create(
            product=cls.product, pack_size=1, code='CD1-20L', barcode='94000',
            recommended_retail_price=10)

    def get(self, url, **params):
        response = self.client.get(
            url, params, HTTP_AUTHORIZATION=f'Token {self.token}',
            HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        return response.json()

    def customers(self, term):
        rows = self.get(reverse('dashboard_customer_search'), q=term)['results']
        return [row['id'] for row in rows]

    def test_customer_found_by_contact_phone_address_group_and_distributor(self):
        for term in ('Dana', 'dana@kiwicafe', '0279999', '021555', 'Quay',
                     'Wharf', 'Southern'):
            self.assertEqual(self.customers(term), [self.customer.pk], term)

    def test_customer_found_by_words_from_different_fields(self):
        self.assertEqual(self.customers('tane kiwi'), [self.customer.pk])

    def test_customer_with_two_contacts_appears_once(self):
        CustomerContact.objects.create(
            customer=self.customer, name='Dana Two', role='Owner')
        self.assertEqual(self.customers('dana'), [self.customer.pk])

    def test_customer_picker_narrows_to_a_distributor(self):
        rows = self.get(
            reverse('dashboard_customer_search'),
            distributor=self.distributor.pk)['results']
        self.assertEqual([row['id'] for row in rows], [self.customer.pk])

    def test_customer_list_and_group_list(self):
        rows = self.get('/staff-api/customers/', q='dana hill')['data']['customers']
        self.assertEqual([row['id'] for row in rows], [self.customer.pk])
        rows = self.get('/staff-api/groups/', q='south')['data']['groups']
        self.assertEqual([row['id'] for row in rows], [self.group.pk])

    def test_group_customer_picker_uses_the_same_fields(self):
        rows = self.get(reverse('dashboard_group_customer_search'), q='0279999')['results']
        self.assertEqual([row['id'] for row in rows], [self.customer.pk])

    def test_product_found_by_range_and_subheading(self):
        for term in ('Foodsafe', 'kitchens'):
            rows = self.get(reverse('dashboard_product_search'), q=term)['results']
            self.assertEqual([row['id'] for row in rows], [self.product.pk], term)

    def test_product_list_finds_a_product_word_and_a_variant_word(self):
        rows = self.get('/staff-api/products/', q='citrus 20L')['data']['products']
        self.assertEqual([row['id'] for row in rows], [self.product.pk])

    def test_variant_picker_finds_a_product_word_and_a_code_word(self):
        rows = self.get(reverse('dashboard_variant_search'), q='degreaser cd1')['results']
        self.assertEqual([row['id'] for row in rows], [self.variant.pk])

    def test_order_found_by_notes_and_by_a_product_on_a_line(self):
        order = CustomerOrder.objects.create(
            customer=self.customer, order_number='ORD-1', notes='Deliver to rear door')
        for _ in range(2):
            OrderLineItem.objects.create(
                order=order, product_variant=self.variant, quantity=1)
        for term in ('rear door', 'degreaser', 'CD1-20L'):
            rows = self.get('/staff-api/orders/', q=term)['data']['orders']
            self.assertEqual([row['id'] for row in rows], [order.pk], term)

    def test_quote_found_by_a_product_on_a_line_and_by_its_author(self):
        quote = Quote.objects.create(
            quote_number='P-1', company_name='Prospect Co', contact_name='Lee',
            address='9 Hill Road', created_by=self.staff)
        QuoteLine.objects.create(
            quote=quote, product_variant=self.variant, product_name='Citrus Degreaser',
            product_code='CD1', price=10)
        for term in ('citrus', 'hill road', 'sam staff'):
            rows = self.get('/staff-api/quotes/', q=term)['data']['quotes']
            self.assertEqual([row['id'] for row in rows], [quote.pk], term)

    def test_ticket_found_by_reply_report_and_people(self):
        report_type = ReportType.objects.create(name='Hygiene audit', created_by=self.staff)
        report = Report.objects.create(
            report_type=report_type, document_number='HA-77', prepared_by=self.staff)
        ticket = Ticket.objects.create(
            created_by=self.staff, customer=self.customer, subject='Pump',
            body='Drips', source_report=report, assigned_to=self.staff)
        TicketReply.objects.create(ticket=ticket, author=self.staff, body='Booked a technician')
        TicketReply.objects.create(ticket=ticket, author=self.staff, body='Technician came')
        for term in ('technician', 'HA-77', 'sam staff'):
            rows = self.get('/staff-api/tickets/', q=term)['data']['tickets']
            self.assertEqual([row['id'] for row in rows], [ticket.pk], term)

    def test_report_found_by_type_and_preparer(self):
        report_type = ReportType.objects.create(name='Hygiene audit', created_by=self.staff)
        report = Report.objects.create(
            report_type=report_type, document_number='HA-78', prepared_by=self.staff,
            customer=self.customer, status='approved')
        for term in ('hygiene', 'sam staff', 'hygiene kiwi'):
            rows = self.get('/reports/staff-api/reports/', q=term)['data']['reports']
            self.assertEqual([row['id'] for row in rows], [report.pk], term)

    def test_user_found_by_business_and_distributor(self):
        rows = self.get('/staff-api/users/', q='kiwi cafe')['data']['users']
        self.assertEqual([row['username'] for row in rows], ['kiwi-owner'])
        rows = self.get('/staff-api/users/', q='southern tane')['data']['users']
        self.assertEqual([row['username'] for row in rows], ['kiwi-owner'])

    def test_distributor_found_by_phone_and_address(self):
        for term in ('034444', 'depot'):
            rows = self.get('/staff-api/distributors/', q=term)['data']['results']
            self.assertEqual([row['id'] for row in rows], [self.distributor.pk], term)
