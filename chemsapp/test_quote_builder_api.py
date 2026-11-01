"""The proposal builder's JSON API, as the admin app calls it."""
import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import (
    ApplicationType, Customer, DilutionVariant, PricingVariant, Product,
    ProductVariant, Size,
)
from quotes.models import Quote


class QuoteBuilderTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('seller', password='pw12345678', is_staff=True)
        self.token = Token.objects.get(user=self.staff).key
        size = Size.objects.create(name='5L', desc='5 litre', amount='5', volume_litres='5.000')
        self.product = Product.objects.create(
            name='Zeal', description='d', directions='d', productCode='ZE', application='<p>Spray.</p>')
        self.variant = ProductVariant.objects.create(
            product=self.product, size=size, pack_size=1, code='ZE5', recommended_retail_price='40.00')
        spray = ApplicationType.objects.create(
            name='Spray bottle', is_active=True, unit_label='per bottle', unit_volume_litres='0.75')
        self.dilution = DilutionVariant.objects.create(
            variant=self.variant, application_type=spray, value='50')
        other = ProductVariant.objects.create(product=self.product, pack_size=1, code='ZE1')
        self.foreign_dilution = DilutionVariant.objects.create(
            variant=other, application_type=spray, value='20')
        user = User.objects.create(username='cafe', email='cafe@example.com')
        self.customer = Customer.objects.create(
            user=user, phoneNumber='1', businessName='Uno Cafe', address='1 Road')

    def call(self, name, args=(), body=None, method='post'):
        url = reverse(name, args=args)
        headers = {'HTTP_ACCEPT': 'application/json', 'HTTP_AUTHORIZATION': f'Token {self.token}'}
        if method == 'get':
            return self.client.get(url, body or {}, **headers)
        return self.client.post(url, json.dumps(body or {}), content_type='application/json', **headers)

    def test_catalogue_nests_variants_and_dilutions(self):
        data = self.call('staff_api_quote_catalogue', method='get').json()['data']
        zeal = next(p for p in data['catalogue'] if p['name'] == 'Zeal')
        five = next(v for v in zeal['variants'] if v['id'] == self.variant.pk)
        self.assertEqual(five['dilution_options'][0]['id'], self.dilution.pk)
        self.assertIn('Uno Cafe', [c['name'] for c in data['customers']])

    def test_price_prefers_the_customers_own(self):
        rrp = self.call('staff_api_quote_price', body={'variant': self.variant.pk}, method='get').json()['data']
        self.assertEqual(rrp, {'price': '40.00', 'source': 'Recommended retail price'})

        own = PricingVariant.objects.create(product_variant=self.variant, price='31.00', name='Contract')
        own.customers.add(self.customer)
        data = self.call('staff_api_quote_price', body={
            'variant': self.variant.pk, 'customer': self.customer.pk}, method='get').json()['data']
        self.assertEqual(data, {'price': '31.00', 'source': 'Customer price (Contract)'})

    @mock.patch('quotes.services.QuotePDFGenerator')
    def test_create_freezes_the_lines(self, _pdf):
        response = self.call('staff_api_quote_create', body={
            'company_name': 'Uno Cafe', 'customer': self.customer.pk, 'contact_name': 'Sam',
            'lines': [{'variant': self.variant.pk, 'price': '35.00', 'dilution': self.dilution.pk},
                      {'variant': '', 'price': ''}],
        })
        self.assertEqual(response.status_code, 200)
        quote = Quote.objects.get(pk=response.json()['data']['id'])
        line = quote.lines.get()
        self.assertEqual((line.product_name, str(line.price)), ('Zeal', '35.00'))
        self.assertEqual(quote.customer, self.customer)
        self.assertEqual(len(line.cost_in_use), 1)

    def test_create_refuses_a_dilution_of_another_variant(self):
        response = self.call('staff_api_quote_create', body={
            'company_name': 'Uno Cafe',
            'lines': [{'variant': self.variant.pk, 'price': '35', 'dilution': self.foreign_dilution.pk}],
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('does not belong', response.json()['errors']['lines'][0])
        self.assertFalse(Quote.objects.exists())

    def test_create_needs_a_company_and_a_line(self):
        no_company = self.call('staff_api_quote_create', body={
            'lines': [{'variant': self.variant.pk, 'price': '35'}]})
        self.assertIn('company_name', no_company.json()['errors'])
        no_lines = self.call('staff_api_quote_create', body={'company_name': 'Uno', 'lines': []})
        self.assertIn('lines', no_lines.json()['errors'])

    def test_a_zero_price_is_refused(self):
        response = self.call('staff_api_quote_create', body={
            'company_name': 'Uno', 'lines': [{'variant': self.variant.pk, 'price': '0'}]})
        self.assertEqual(response.status_code, 400)

    @mock.patch('quotes.services.send_quote_pdf_email')
    @mock.patch('quotes.services.QuotePDFGenerator')
    def test_email_checks_the_address_then_sends(self, _pdf, send):
        quote = Quote.objects.create(company_name='Uno', created_by=self.staff)
        bad = self.call('staff_api_quote_email', [quote.pk], {'email_address': 'nope'})
        self.assertEqual(bad.status_code, 400)
        send.assert_not_called()

        good = self.call('staff_api_quote_email', [quote.pk], {'email_address': 'sam@uno.example'})
        self.assertEqual(good.status_code, 200)
        send.assert_called_once_with(quote, 'sam@uno.example')

    def test_delete(self):
        quote = Quote.objects.create(company_name='Uno', created_by=self.staff)
        self.call('staff_api_quote_delete', [quote.pk])
        self.assertFalse(Quote.objects.filter(pk=quote.pk).exists())

    def test_non_staff_is_refused(self):
        outsider = User.objects.create_user('outsider', password='pw12345678')
        response = self.client.get(
            reverse('staff_api_quote_catalogue'), HTTP_ACCEPT='application/json',
            HTTP_AUTHORIZATION=f'Token {Token.objects.get(user=outsider).key}')
        self.assertEqual(response.status_code, 403)
