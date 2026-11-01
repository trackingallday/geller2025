"""The distributor screen's endpoints, as the admin app calls them."""
import json

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import Customer, Distributor


class DistributorTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('office', password='pw12345678', is_staff=True)
        self.token = Token.objects.get(user=self.staff).key
        self.distributor = Distributor.objects.create(businessname='Otago Supplies')
        self.rep = User.objects.create_user('rep', email='rep@example.com', password='pw12345678')
        self.no_email = User.objects.create_user('quiet', password='pw12345678')
        self.customer = Customer.objects.create(
            user=User.objects.create(username='cafe'), phoneNumber='1', businessName='Uno Cafe', address='1')

    def call(self, name, body=None, method='post'):
        headers = {'HTTP_ACCEPT': 'application/json', 'HTTP_AUTHORIZATION': f'Token {self.token}'}
        url = reverse(name, args=[self.distributor.pk])
        if method == 'get':
            return self.client.get(url, **headers)
        return self.client.post(url, json.dumps(body or {}), content_type='application/json', **headers)

    def test_link_and_unlink_people_and_customers(self):
        data = self.call('staff_api_distributor_user_link', {'id': self.rep.pk}).json()['data']
        self.assertEqual([u['username'] for u in data['users']], ['rep'])
        data = self.call('staff_api_distributor_customer_link', {'id': self.customer.pk}).json()['data']
        self.assertEqual([c['name'] for c in data['customers']], ['Uno Cafe'])

        data = self.call('staff_api_distributor_user_link', {'id': self.rep.pk, 'remove': True}).json()['data']
        self.assertEqual(data['users'], [])

    def test_an_unknown_record_is_refused(self):
        self.assertEqual(self.call('staff_api_distributor_user_link', {'id': 999999}).status_code, 404)

    def test_resets_go_to_everyone_with_an_email(self):
        self.distributor.users.add(self.rep, self.no_email)
        data = self.call('staff_api_distributor_send_resets').json()['data']
        self.assertEqual(data, {'sent': ['rep'], 'skipped': ['quiet']})
        self.assertEqual([m.to for m in mail.outbox], [['rep@example.com']])

    def test_detail(self):
        self.distributor.users.add(self.rep)
        data = self.call('staff_api_distributor_detail', method='get').json()['data']
        self.assertEqual(data['name'], 'Otago Supplies')
        self.assertEqual(data['users'][0]['email'], 'rep@example.com')
