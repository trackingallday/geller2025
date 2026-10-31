"""The staff gate must answer in JSON, for a token or a session alike."""
import json

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from rest_framework.authtoken.models import Token

from .staff_api import form_data, json_body, staff_api, wants_json


def body(response):
    """Decode a raw JsonResponse. RequestFactory gives no .json() helper."""
    return json.loads(response.content)


@staff_api
def _probe(request):
    """A view that only reports who got through."""
    from django.http import JsonResponse
    return JsonResponse({'ok': True, 'who': request.user.username})


class StaffApiDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.staff = User.objects.create_user(
            'gate-staff', password='pw', is_staff=True)
        self.plain = User.objects.create_user('gate-plain', password='pw')

    def test_anonymous_gets_401_as_json(self):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = _probe(request)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertFalse(body(response)['ok'])

    def test_session_staff_passes(self):
        request = self.factory.get('/')
        request.user = self.staff
        response = _probe(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body(response)['who'], 'gate-staff')

    def test_session_non_staff_gets_403(self):
        request = self.factory.get('/')
        request.user = self.plain
        response = _probe(request)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_token_staff_passes(self):
        token, _ = Token.objects.get_or_create(user=self.staff)
        request = self.factory.get(
            '/', HTTP_AUTHORIZATION=f'Token {token.key}')
        response = _probe(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body(response)['who'], 'gate-staff')

    def test_token_non_staff_gets_403(self):
        token, _ = Token.objects.get_or_create(user=self.plain)
        request = self.factory.get(
            '/', HTTP_AUTHORIZATION=f'Token {token.key}')
        response = _probe(request)
        self.assertEqual(response.status_code, 403)

    def test_unknown_token_gets_401(self):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get('/', HTTP_AUTHORIZATION='Token nope')
        request.user = AnonymousUser()
        response = _probe(request)
        self.assertEqual(response.status_code, 401)

    def test_token_wins_over_an_anonymous_session(self):
        """A token must authenticate even with no session cookie present."""
        from django.contrib.auth.models import AnonymousUser
        token, _ = Token.objects.get_or_create(user=self.staff)
        request = self.factory.get(
            '/', HTTP_AUTHORIZATION=f'Token {token.key}')
        request.user = AnonymousUser()
        response = _probe(request)
        self.assertEqual(response.status_code, 200)

    def test_inactive_staff_is_refused(self):
        self.staff.is_active = False
        self.staff.save()
        token, _ = Token.objects.get_or_create(user=self.staff)
        request = self.factory.get(
            '/', HTTP_AUTHORIZATION=f'Token {token.key}')
        response = _probe(request)
        self.assertEqual(response.status_code, 403)


class RequestHelperTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_wants_json_follows_the_accept_header(self):
        self.assertTrue(wants_json(
            self.factory.get('/', HTTP_ACCEPT='application/json')))
        self.assertFalse(wants_json(
            self.factory.get('/', HTTP_ACCEPT='text/html')))
        self.assertFalse(wants_json(self.factory.get('/')))

    def test_json_body_reads_a_dict_and_shrugs_at_junk(self):
        request = self.factory.post(
            '/', data='{"a": 1}', content_type='application/json')
        self.assertEqual(json_body(request), {'a': 1})

        broken = self.factory.post(
            '/', data='not json', content_type='application/json')
        self.assertEqual(json_body(broken), {})

        a_list = self.factory.post(
            '/', data='[1,2]', content_type='application/json')
        self.assertEqual(json_body(a_list), {})

    def test_form_data_handles_both_content_types(self):
        as_json = self.factory.post(
            '/', data='{"name": "x"}', content_type='application/json')
        self.assertEqual(form_data(as_json)['name'], 'x')

        as_form = self.factory.post('/', data={'name': 'y'})
        self.assertEqual(form_data(as_form)['name'], 'y')
