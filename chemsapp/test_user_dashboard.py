"""The staff user-management endpoints."""
import json

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import Distributor, Profile


class UserDashboardTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            'u-staff', password='pw', email='staff@example.com', is_staff=True)
        self.client.force_login(self.staff)

        self.plain = User.objects.create_user(
            'u-plain', password='pw', email='plain@example.com',
            first_name='Plain', last_name='Person')
        profile = Profile.objects.get(user=self.plain)
        profile.profileType = 'customer'
        profile.businessName = 'Plain Co'
        profile.address = '1 Road'
        profile.phoneNumber = '555'
        profile.save()

        self.distributor = Distributor.objects.create(businessname='Acme Dist')

    def get_json(self, url, **params):
        response = self.client.get(url, params, HTTP_ACCEPT='application/json')
        return response, json.loads(response.content)

    def post_json(self, url, payload):
        response = self.client.post(
            url, data=json.dumps(payload),
            content_type='application/json', HTTP_ACCEPT='application/json')
        return response, json.loads(response.content)

    # --- listing ---

    def test_list_returns_users_with_their_profile(self):
        response, data = self.get_json(reverse('staff_api_user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['ok'])
        names = {u['username'] for u in data['data']['users']}
        self.assertIn('u-plain', names)
        row = next(u for u in data['data']['users'] if u['username'] == 'u-plain')
        self.assertEqual(row['profile']['business_name'], 'Plain Co')

    def test_list_searches_name_and_email(self):
        _, by_email = self.get_json(reverse('staff_api_user_list'), q='plain@')
        self.assertEqual(
            [u['username'] for u in by_email['data']['users']], ['u-plain'])

        _, by_name = self.get_json(reverse('staff_api_user_list'), q='Plain')
        self.assertIn('u-plain',
                      [u['username'] for u in by_name['data']['users']])

    def test_list_filters_by_staff_role(self):
        _, data = self.get_json(reverse('staff_api_user_list'), role='staff')
        names = {u['username'] for u in data['data']['users']}
        self.assertIn('u-staff', names)
        self.assertNotIn('u-plain', names)

    def test_list_filters_by_profile_type(self):
        _, data = self.get_json(reverse('staff_api_user_list'), role='customer')
        self.assertIn('u-plain',
                      [u['username'] for u in data['data']['users']])

    def test_list_refuses_a_non_staff_caller(self):
        self.client.force_login(self.plain)
        response = self.client.get(
            reverse('staff_api_user_list'), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 403)

    # --- detail ---

    def test_detail_returns_one_user(self):
        response, data = self.get_json(
            reverse('staff_api_user_detail', args=[self.plain.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['data']['username'], 'u-plain')

    # --- creation ---

    def test_create_makes_a_user_and_sends_a_reset(self):
        response, data = self.post_json(reverse('staff_api_create_user'), {
            'username': 'u-new',
            'email': 'new@example.com',
            'first_name': 'New',
            'is_staff': True,
            'profile_type': 'admin',
            'business_name': 'New Co',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['data']['is_staff'])

        made = User.objects.get(username='u-new')
        # The password is random and never disclosed, so the reset email is
        # the only way in. It must stay *usable*, or the reset form would
        # refuse to email this account at all.
        self.assertTrue(made.has_usable_password())
        self.assertFalse(made.check_password(''))
        self.assertEqual(made.profile.businessName, 'New Co')
        self.assertTrue(data['data']['reset_email_sent'])
        self.assertEqual(len(mail.outbox), 1)

    def test_create_can_link_a_distributor(self):
        _, data = self.post_json(reverse('staff_api_create_user'), {
            'username': 'u-dist',
            'email': 'dist@example.com',
            'distributor_id': self.distributor.pk,
            'send_reset_email': False,
        })
        self.assertEqual(
            [d['name'] for d in data['data']['distributors']], ['Acme Dist'])

    def test_create_refuses_a_duplicate_username(self):
        response, data = self.post_json(reverse('staff_api_create_user'), {
            'username': 'u-plain', 'email': 'other@example.com'})
        self.assertEqual(response.status_code, 409)
        self.assertFalse(data['ok'])

    def test_create_refuses_a_duplicate_email(self):
        response, _ = self.post_json(reverse('staff_api_create_user'), {
            'username': 'u-other', 'email': 'plain@example.com'})
        self.assertEqual(response.status_code, 409)

    def test_create_requires_a_username(self):
        response, _ = self.post_json(
            reverse('staff_api_create_user'), {'email': 'x@example.com'})
        self.assertEqual(response.status_code, 400)

    def test_create_refuses_an_unknown_distributor(self):
        response, _ = self.post_json(reverse('staff_api_create_user'), {
            'username': 'u-bad', 'distributor_id': 999999})
        self.assertEqual(response.status_code, 400)

    # --- updating ---

    def test_update_changes_only_the_fields_sent(self):
        url = reverse('staff_api_update_user', args=[self.plain.pk])
        response, data = self.post_json(url, {'is_staff': True})
        self.assertEqual(response.status_code, 200)

        self.plain.refresh_from_db()
        self.assertTrue(self.plain.is_staff)
        # Untouched fields survive.
        self.assertEqual(self.plain.first_name, 'Plain')
        self.assertEqual(self.plain.email, 'plain@example.com')

    def test_update_edits_the_profile_too(self):
        url = reverse('staff_api_update_user', args=[self.plain.pk])
        self.post_json(url, {'business_name': 'Renamed Co'})
        self.assertEqual(
            Profile.objects.get(user=self.plain).businessName, 'Renamed Co')

    def test_update_refuses_a_superuser_who_is_not_staff(self):
        url = reverse('staff_api_update_user', args=[self.plain.pk])
        response, data = self.post_json(url, {'is_superuser': True})
        self.assertEqual(response.status_code, 400)
        self.assertIn('staff', data['detail'])

    def test_update_refuses_a_taken_username(self):
        url = reverse('staff_api_update_user', args=[self.plain.pk])
        response, _ = self.post_json(url, {'username': 'u-staff'})
        self.assertEqual(response.status_code, 409)

    def test_update_can_deactivate(self):
        url = reverse('staff_api_update_user', args=[self.plain.pk])
        self.post_json(url, {'is_active': False})
        self.plain.refresh_from_db()
        self.assertFalse(self.plain.is_active)

    # --- password reset ---

    def test_send_reset_emails_the_user(self):
        url = reverse('staff_api_send_password_reset', args=[self.plain.pk])
        response, data = self.post_json(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['data']['reset_email_sent'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('plain@example.com', mail.outbox[0].to)

    def test_send_reset_needs_an_email_address(self):
        no_email = User.objects.create_user('u-noemail', password='pw')
        url = reverse('staff_api_send_password_reset', args=[no_email.pk])
        response, _ = self.post_json(url, {})
        self.assertEqual(response.status_code, 400)

    # --- distributor picker ---

    def test_distributor_list_searches_by_business_name(self):
        _, data = self.get_json(
            reverse('staff_api_distributor_list'), q='Acme')
        self.assertEqual(
            [d['name'] for d in data['data']['results']], ['Acme Dist'])

    # --- token auth ---

    def test_a_staff_token_works_without_a_session(self):
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=self.staff)
        self.client.logout()
        response = self.client.get(
            reverse('staff_api_user_list'),
            HTTP_ACCEPT='application/json',
            HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertEqual(response.status_code, 200)
