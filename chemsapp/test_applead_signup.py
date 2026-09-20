"""Tests for the self-serve, code-verified AppLead signup."""
import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token

from chemsapp.models import AppLeadSignupCode, Customer, Distributor


class AppLeadSignupStartTests(TestCase):
    def setUp(self):
        self.url = reverse('applead_signup_start')

    def _post(self, **overrides):
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'password': 'a-strong-password',
            'business_name': 'Acme Cleaning',
        }
        data.update(overrides)
        return self.client.post(
            self.url, data=json.dumps(data), content_type='application/json')

    @patch('chemsapp.views.PostmarkClient')
    def test_creates_a_pending_code_and_sends_an_email(self, mock_postmark_client):
        response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        pending = AppLeadSignupCode.objects.get(email='jane@example.com')
        self.assertEqual(len(pending.code), 6)
        self.assertTrue(pending.code.isdigit())
        self.assertFalse(pending.consumed)
        self.assertFalse(User.objects.filter(email='jane@example.com').exists())

        mock_postmark_client.return_value.emails.Email.assert_called_once()
        sent_kwargs = mock_postmark_client.return_value.emails.Email.call_args.kwargs
        self.assertEqual(sent_kwargs['To'], 'jane@example.com')
        self.assertIn(pending.code, sent_kwargs['TextBody'])

    @patch('chemsapp.views.PostmarkClient')
    def test_a_second_signup_replaces_the_first_pending_code(self, mock_postmark_client):
        self._post()
        first_code = AppLeadSignupCode.objects.get(email='jane@example.com').code
        self._post()
        codes = AppLeadSignupCode.objects.filter(email='jane@example.com', consumed=False)
        self.assertEqual(codes.count(), 1)

    def test_rejects_a_duplicate_email(self):
        User.objects.create_user(username='jane@example.com', email='jane@example.com')
        response = self._post()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AppLeadSignupCode.objects.filter(email='jane@example.com').exists())

    def test_rejects_a_short_password(self):
        response = self._post(password='short')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AppLeadSignupCode.objects.exists())

    def test_rejects_a_missing_email(self):
        response = self._post(email='')
        self.assertEqual(response.status_code, 400)

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @patch('chemsapp.views.PostmarkClient')
    def test_email_failure_does_not_leave_a_pending_code(self, mock_postmark_client):
        mock_postmark_client.return_value.emails.Email.return_value.send.side_effect = (
            Exception('Postmark is down'))
        response = self._post()
        self.assertEqual(response.status_code, 502)
        self.assertFalse(AppLeadSignupCode.objects.filter(email='jane@example.com').exists())


class AppLeadSignupVerifyTests(TestCase):
    def setUp(self):
        self.start_url = reverse('applead_signup_start')
        self.verify_url = reverse('applead_signup_verify')

    @patch('chemsapp.views.PostmarkClient')
    def _start_signup(self, mock_postmark_client, **overrides):
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'password': 'a-strong-password',
            'business_name': 'Acme Cleaning',
        }
        data.update(overrides)
        self.client.post(self.start_url, data=json.dumps(data), content_type='application/json')
        return AppLeadSignupCode.objects.get(email=data['email'])

    def _verify(self, email, code):
        return self.client.post(
            self.verify_url, data=json.dumps({'email': email, 'code': code}),
            content_type='application/json')

    def test_correct_code_creates_the_user_with_an_applead_profile(self):
        pending = self._start_signup()
        response = self._verify('jane@example.com', pending.code)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['profileType'], 'applead')
        self.assertTrue(body['token'])

        user = User.objects.get(email='jane@example.com')
        self.assertEqual(user.username, 'jane@example.com')
        self.assertTrue(user.check_password('a-strong-password'))
        self.assertEqual(user.profile.profileType, 'applead')
        self.assertEqual(user.profile.businessName, 'Acme Cleaning')

        self.assertFalse(Customer.objects.filter(user=user).exists())
        self.assertFalse(Distributor.objects.filter(users=user).exists())

        pending.refresh_from_db()
        self.assertTrue(pending.consumed)

    def test_returns_a_token_that_authenticates(self):
        pending = self._start_signup()
        response = self._verify('jane@example.com', pending.code)
        token_key = response.json()['token']
        user = User.objects.get(email='jane@example.com')
        self.assertEqual(Token.objects.get(user=user).key, token_key)

    def test_wrong_code_is_rejected(self):
        self._start_signup()
        response = self._verify('jane@example.com', '000000')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email='jane@example.com').exists())

    def test_expired_code_is_rejected(self):
        pending = self._start_signup()
        pending.expires_at = timezone.now() - timedelta(minutes=1)
        pending.save()
        response = self._verify('jane@example.com', pending.code)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email='jane@example.com').exists())

    def test_a_code_cannot_be_used_twice(self):
        pending = self._start_signup()
        self._verify('jane@example.com', pending.code)
        response = self._verify('jane@example.com', pending.code)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.filter(email='jane@example.com').count(), 1)

    def test_business_name_is_optional(self):
        pending = self._start_signup(business_name='')
        self._verify('jane@example.com', pending.code)
        user = User.objects.get(email='jane@example.com')
        self.assertEqual(user.profile.businessName, 'Jane Doe')

    def test_get_is_not_allowed(self):
        response = self.client.get(self.verify_url)
        self.assertEqual(response.status_code, 405)


class AppLeadUserProfileApiTests(TestCase):
    @patch('chemsapp.views.PostmarkClient')
    def test_get_user_profile_api_returns_applead_shape(self, mock_postmark_client):
        self.client.post(
            reverse('applead_signup_start'),
            data=json.dumps({
                'first_name': 'Jane', 'last_name': 'Doe',
                'email': 'jane@example.com', 'password': 'a-strong-password',
            }),
            content_type='application/json')
        pending = AppLeadSignupCode.objects.get(email='jane@example.com')
        verify_response = self.client.post(
            reverse('applead_signup_verify'),
            data=json.dumps({'email': 'jane@example.com', 'code': pending.code}),
            content_type='application/json')
        token = verify_response.json()['token']

        profile_response = self.client.get(
            reverse('reports:api_user_profile'),
            HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(profile_response.status_code, 200)
        body = profile_response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['profileType'], 'applead')
