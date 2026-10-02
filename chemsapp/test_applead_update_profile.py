"""Tests for self-service AppLead profile (name) updates."""
import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import AppLeadSignupCode


class AppLeadUpdateProfileTests(TestCase):
    def setUp(self):
        self.url = reverse('applead_update_profile')

    @patch('chemsapp.views.PostmarkClient')
    def _create_applead_user(self, mock_postmark_client, email='jane@example.com'):
        self.client.post(
            reverse('applead_signup_start'),
            data=json.dumps({
                'first_name': 'Jane', 'last_name': 'Doe', 'email': email,
                'password': 'a-strong-password', 'business_name': 'Acme Cleaning',
            }),
            content_type='application/json')
        pending = AppLeadSignupCode.objects.get(email=email)
        response = self.client.post(
            reverse('applead_signup_verify'),
            data=json.dumps({'email': email, 'code': pending.code}),
            content_type='application/json')
        body = response.json()
        return User.objects.get(email=email), body['token']

    def _update(self, token, **data):
        return self.client.post(
            self.url, data=json.dumps(data), content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {token}')

    def test_rejects_unauthenticated_requests(self):
        response = self.client.post(
            self.url, data=json.dumps({'first_name': 'A', 'last_name': 'B'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_updates_first_and_last_name(self):
        user, token = self._create_applead_user()

        response = self._update(token, first_name='Janet', last_name='Smith')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['first_name'], 'Janet')
        self.assertEqual(body['last_name'], 'Smith')

        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Janet')
        self.assertEqual(user.last_name, 'Smith')

    def test_rejects_a_missing_first_name(self):
        user, token = self._create_applead_user()
        response = self._update(token, first_name='', last_name='Smith')
        self.assertEqual(response.status_code, 400)

    def test_rejects_a_missing_last_name(self):
        user, token = self._create_applead_user()
        response = self._update(token, first_name='Janet', last_name='')
        self.assertEqual(response.status_code, 400)

    def test_rejects_a_non_applead_user(self):
        user = User.objects.create_user(
            username='staffer', email='staffer@example.com', password='a-strong-password')
        user.profile.profileType = 'customer'
        user.profile.save()
        token, _ = Token.objects.get_or_create(user=user)

        response = self._update(token.key, first_name='A', last_name='B')

        self.assertEqual(response.status_code, 403)

    def test_get_is_not_allowed(self):
        user, token = self._create_applead_user()
        response = self.client.get(self.url, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 405)
