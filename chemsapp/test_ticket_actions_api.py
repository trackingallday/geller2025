"""The tickets screen's actions, as the admin app calls them."""
import json
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import Customer, Distributor
from tickets.models import Ticket


class TicketActionTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('helpdesk', password='pw12345678', is_staff=True)
        self.token = Token.objects.get(user=self.staff).key
        user = User.objects.create(username='cafe', email='cafe@example.com')
        self.customer = Customer.objects.create(
            user=user, phoneNumber='1', businessName='Uno Cafe', address='1 Road')
        self.distributor = Distributor.objects.create(businessname='Otago Supplies')
        self.distributor.customers.add(self.customer)
        self.rep = User.objects.create(username='rep', first_name='Sam', last_name='Rep')
        self.distributor.users.add(self.rep)
        self.ticket = Ticket.objects.create(
            created_by=self.staff, customer=self.customer, subject='Leak', body='Drips', status='read')

    def call(self, name, args=(), body=None, method='post'):
        headers = {'HTTP_ACCEPT': 'application/json', 'HTTP_AUTHORIZATION': f'Token {self.token}'}
        url = reverse(name, args=args)
        if method == 'get':
            return self.client.get(url, body or {}, **headers)
        return self.client.post(url, json.dumps(body or {}), content_type='application/json', **headers)

    def test_create_with_an_assignee(self):
        data = self.call('staff_api_ticket_create', body={
            'customer': self.customer.pk, 'subject': 'Dispenser', 'body': 'Broken', 'assigned_to': self.rep.pk,
        }).json()['data']
        self.assertEqual(data['assigned_to'], 'rep')
        self.assertEqual(data['customer']['id'], self.customer.pk)

    def test_create_names_each_missing_field(self):
        errors = self.call('staff_api_ticket_create', body={}).json()['errors']
        self.assertEqual(set(errors), {'customer', 'subject', 'body'})

    def test_status_must_be_a_real_one(self):
        bad = self.call('staff_api_ticket_update', [self.ticket.pk], {'status': 'lost'})
        self.assertEqual(bad.status_code, 400)
        good = self.call('staff_api_ticket_update', [self.ticket.pk], {'status': 'completed'})
        self.assertEqual(good.json()['data']['status'], 'completed')

    def test_assign_and_unassign(self):
        self.call('staff_api_ticket_update', [self.ticket.pk], {'assigned_to': self.rep.pk})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.rep)
        self.call('staff_api_ticket_update', [self.ticket.pk], {'assigned_to': None})
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.assigned_to)

    def test_a_reply_puts_a_read_ticket_back_to_pending(self):
        data = self.call('staff_api_ticket_reply', [self.ticket.pk], {'body': 'On my way'}).json()['data']
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(data['replies'][-1]['body'], 'On my way')
        self.assertTrue(data['replies'][-1]['is_self'])

    def test_an_empty_reply_is_refused(self):
        response = self.call('staff_api_ticket_reply', [self.ticket.pk], {'body': '  '})
        self.assertIn('body', response.json()['errors'])

    @override_settings(MEDIA_ROOT='/tmp/geller-ticket-test-media')
    @mock.patch('chemsapp.views.downscale_image')
    def test_an_image_attaches_and_bumps_the_ticket(self, _downscale):
        gif = SimpleUploadedFile('photo.gif', b'GIF89a\x01\x00\x01\x00\x00\x00\x00;', content_type='image/gif')
        response = self.client.post(
            reverse('staff_api_ticket_image', args=[self.ticket.pk]), {'image': gif},
            HTTP_ACCEPT='application/json', HTTP_AUTHORIZATION=f'Token {self.token}')
        data = response.json()['data']
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['status'], 'pending')

    def test_the_assign_cascade(self):
        distributors = self.call(
            'staff_api_customer_distributors', [self.customer.pk], method='get').json()['data']['distributors']
        self.assertEqual(distributors, [{'id': self.distributor.pk, 'name': 'Otago Supplies'}])
        users = self.call('staff_api_distributor_users', [self.distributor.pk], method='get').json()['data']['users']
        self.assertEqual(users, [{'id': self.rep.pk, 'name': 'Sam Rep (rep)'}])

    def test_the_list_filters_by_distributor(self):
        other = Customer.objects.create(
            user=User.objects.create(username='x'), phoneNumber='1', businessName='Other', address='2')
        Ticket.objects.create(created_by=self.staff, customer=other, subject='Elsewhere', body='b')
        rows = self.call('staff_api_ticket_list', body={'distributor': self.distributor.pk}, method='get').json()['data']['tickets']
        self.assertEqual([r['subject'] for r in rows], ['Leak'])
