"""Tests for self-service AppLead account deletion."""
import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from ai.models import AIThread
from chemsapp.models import AppLeadSignupCode
from reports.models import Report, ReportType
from tickets.models import Ticket


class AppLeadDeleteAccountTests(TestCase):
    def setUp(self):
        self.url = reverse('applead_delete_account')

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

    def _delete(self, token):
        return self.client.post(
            self.url, content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {token}')

    def test_rejects_unauthenticated_requests(self):
        response = self.client.post(self.url, content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_rejects_an_invalid_token(self):
        response = self.client.post(
            self.url, content_type='application/json',
            HTTP_AUTHORIZATION='Token not-a-real-token')
        self.assertEqual(response.status_code, 401)

    def test_deletes_an_applead_user_with_no_other_records(self):
        user, token = self._create_applead_user()
        user_id = user.id

        response = self._delete(token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_token_is_invalidated_after_deletion(self):
        user, token = self._create_applead_user()
        self._delete(token)

        self.assertFalse(Token.objects.filter(key=token).exists())

        second_response = self._delete(token)
        self.assertEqual(second_response.status_code, 401)

    def test_deleting_twice_fails_the_second_time(self):
        user, token = self._create_applead_user()
        first = self._delete(token)
        self.assertEqual(first.status_code, 200)

        second = self._delete(token)
        self.assertEqual(second.status_code, 401)

    def test_anonymizes_instead_of_hard_deleting_when_a_report_exists(self):
        user, token = self._create_applead_user()
        user_id = user.id
        report_type = ReportType.objects.create(name='Site Visit', created_by=user)
        report = Report.objects.create(report_type=report_type, prepared_by=user)

        response = self._delete(token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})

        # The user row survives (so prepared_by/created_by still resolve),
        # but login is no longer possible and personal data is scrubbed.
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')
        self.assertNotEqual(user.email, 'jane@example.com')
        self.assertFalse(Token.objects.filter(user_id=user_id).exists())

        report.refresh_from_db()
        self.assertEqual(report.prepared_by_id, user_id)

    def test_anonymizes_when_a_ticket_exists(self):
        user, token = self._create_applead_user()
        Ticket.objects.create(subject='Help', body='x', created_by=user)

        response = self._delete(token)

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_anonymizes_when_an_ai_thread_exists(self):
        user, token = self._create_applead_user()
        AIThread.objects.create(user=user)

        response = self._delete(token)

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_rejects_a_non_applead_user(self):
        user = User.objects.create_user(
            username='staffer', email='staffer@example.com', password='a-strong-password')
        user.profile.profileType = 'customer'
        user.profile.save()
        token, _ = Token.objects.get_or_create(user=user)

        response = self._delete(token.key)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(id=user.id).exists())

    def test_get_is_not_allowed(self):
        user, token = self._create_applead_user()
        response = self.client.get(self.url, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 405)
