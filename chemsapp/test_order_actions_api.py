"""The order actions, as the admin app calls them."""
import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import Customer, Product, ProductVariant
from orders.models import CustomerOrder, OrderLineItem


class OrderActionTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('orders', password='pw12345678', is_staff=True)
        self.token = Token.objects.get(user=self.staff).key
        user = User.objects.create(username='cafe', email='cafe@example.com')
        self.customer = Customer.objects.create(
            user=user, phoneNumber='1', businessName='Uno Cafe', address='1 Road')
        product = Product.objects.create(name='Zeal', description='d', directions='d', productCode='ZE')
        self.variant = ProductVariant.objects.create(product=product, pack_size=1, code='ZE5')

    def call(self, name, args=(), body=None):
        return self.client.post(
            reverse(name, args=args), json.dumps(body or {}), content_type='application/json',
            HTTP_ACCEPT='application/json', HTTP_AUTHORIZATION=f'Token {self.token}')

    def test_create_with_lines(self):
        data = self.call('staff_api_order_create', body={
            'customer': self.customer.pk, 'notes': 'Back door',
            'lines': [{'variant': self.variant.pk, 'quantity': 4, 'soh': 1, 'max_stock_level': 6}],
        }).json()['data']
        self.assertFalse(data['submitted'])
        self.assertEqual(data['line_items'][0]['quantity'], 4)
        self.assertEqual(data['notes'], 'Back door')

    def test_a_line_needs_a_product_and_whole_numbers(self):
        no_product = self.call('staff_api_order_create', body={
            'customer': self.customer.pk, 'lines': [{'quantity': 2}]})
        self.assertIn('lines', no_product.json()['errors'])
        negative = self.call('staff_api_order_create', body={
            'customer': self.customer.pk, 'lines': [{'variant': self.variant.pk, 'quantity': -1}]})
        self.assertEqual(negative.status_code, 400)
        self.assertFalse(CustomerOrder.objects.exists())

    def test_update_edits_removes_and_adds_lines(self):
        order = CustomerOrder.objects.create(customer=self.customer)
        line = OrderLineItem.objects.create(order=order, product_variant=self.variant, quantity=1)
        gone = OrderLineItem.objects.create(order=order, product_variant=self.variant, quantity=9)

        data = self.call('staff_api_order_update', [order.pk], {
            'fulfilment_status': 'processing',
            'lines': [
                {'id': line.pk, 'variant': self.variant.pk, 'quantity': 3},
                {'id': gone.pk, 'delete': True},
                {'variant': self.variant.pk, 'quantity': 5},
            ],
        }).json()['data']
        self.assertEqual(data['fulfilment_status'], 'processing')
        self.assertEqual(sorted(l['quantity'] for l in data['line_items']), [3, 5])

    def test_a_status_must_be_a_real_one(self):
        order = CustomerOrder.objects.create(customer=self.customer)
        response = self.call('staff_api_order_update', [order.pk], {'fulfilment_status': 'lost'})
        self.assertEqual(response.status_code, 400)

    @mock.patch('orders.services.OrderPDFGenerator')
    def test_submit_builds_the_pdf_once_and_locks_the_lines(self, generator):
        order = CustomerOrder.objects.create(customer=self.customer)
        OrderLineItem.objects.create(order=order, product_variant=self.variant, quantity=1)

        self.assertTrue(self.call('staff_api_order_submit', [order.pk]).json()['data']['submitted'])
        generator.return_value.generate_and_save.assert_called_once()

        again = self.call('staff_api_order_submit', [order.pk])
        self.assertEqual(again.status_code, 409)
        locked = self.call('staff_api_order_update', [order.pk], {'lines': []})
        self.assertEqual(locked.status_code, 409)
        # Status still changes on a submitted order.
        status = self.call('staff_api_order_update', [order.pk], {'fulfilment_status': 'fulfilled'})
        self.assertEqual(status.status_code, 200)

    def test_an_empty_order_cannot_be_submitted(self):
        order = CustomerOrder.objects.create(customer=self.customer)
        self.assertEqual(self.call('staff_api_order_submit', [order.pk]).status_code, 400)

    @mock.patch('orders.services.send_order_pdf_email')
    def test_email_checks_the_address(self, send):
        order = CustomerOrder.objects.create(customer=self.customer)
        self.assertEqual(self.call('staff_api_order_email', [order.pk], {'email_address': 'x'}).status_code, 400)
        self.call('staff_api_order_email', [order.pk], {'email_address': 'boss@example.com'})
        send.assert_called_once_with(order, 'boss@example.com')

    def test_delete(self):
        order = CustomerOrder.objects.create(customer=self.customer)
        self.call('staff_api_order_delete', [order.pk])
        self.assertFalse(CustomerOrder.objects.exists())
