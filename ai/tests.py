import base64
import json
from unittest.mock import patch

import requests
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token

from ai.models import AIThread, AIMessage


class FakeUpstreamResponse:
    def __init__(self, status_code=200, body=b'', content_type='application/json'):
        self.status_code = status_code
        self.content = body
        self.headers = {'Content-Type': content_type}

    def iter_content(self, chunk_size):
        yield self.content


def json_upstream(payload, status_code=200):
    return FakeUpstreamResponse(status_code=status_code, body=json.dumps(payload).encode('utf-8'))


WORKFLOW_PATH = '/ai/api/workflows/question-router/start-async'
REPLY_PATH = '/ai/api/agents/replyAgent/generate'
COMPETITOR_PATH = '/ai/api/agents/competitor-comparison-agent/generate'


class AIProxyTests(TestCase):
    serialized_rollback = True

    def setUp(self):
        self.user = User.objects.create_user(username='rep', password='pw', email='rep@example.com')
        token, _ = Token.objects.get_or_create(user=self.user)
        self.auth = {'HTTP_AUTHORIZATION': 'Token {}'.format(token.key)}

        self.other_user = User.objects.create_user(username='other', password='pw')
        Token.objects.get_or_create(user=self.other_user)

    def post_json(self, path, payload, **extra):
        return self.client.post(path, data=json.dumps(payload), content_type='application/json',
                                **dict(self.auth, **extra))

    def test_requires_authentication(self):
        with patch('ai.views.requests.request') as mock_request:
            response = self.client.post(REPLY_PATH, data='{}', content_type='application/json')
        self.assertEqual(response.status_code, 401)
        mock_request.assert_not_called()
        self.assertEqual(AIThread.objects.count(), 0)

    def test_generic_passthrough_forwards_and_relays(self):
        upstream = FakeUpstreamResponse(status_code=200, body=b'{"agents": []}')
        with patch('ai.views.requests.request', return_value=upstream) as mock_request:
            response = self.client.get('/ai/api/agents?limit=5', **self.auth)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'{"agents": []}')
        self.assertEqual(response['Content-Type'], 'application/json')

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(args[1], 'http://localhost:4111/api/agents?limit=5')
        self.assertTrue(kwargs['headers']['Authorization'].startswith('Token '))
        self.assertEqual(AIThread.objects.count(), 0)

    def test_first_message_creates_thread(self):
        upstream = json_upstream({'result': {'response': 'Bio-Fuel is a degreaser.'},
                                  'usage': {'input_tokens': 10, 'output_tokens': 5}})
        with patch('ai.views.requests.request', return_value=upstream):
            response = self.post_json(WORKFLOW_PATH, {'inputData': {'question': 'What is Bio-Fuel?'}})

        self.assertEqual(response.status_code, 200)
        thread = AIThread.objects.get()
        self.assertEqual(thread.user, self.user)
        self.assertEqual(thread.kind, 'question')
        self.assertEqual(thread.title, 'What is Bio-Fuel?')

        messages = list(thread.messages.all())
        self.assertEqual([m.role for m in messages], ['user', 'assistant'])
        self.assertEqual(messages[0].content, 'What is Bio-Fuel?')
        self.assertEqual(messages[1].content, 'Bio-Fuel is a degreaser.')
        self.assertEqual(messages[1].metadata['usage'], {'input_tokens': 10, 'output_tokens': 5})

        data = json.loads(response.content)
        self.assertEqual(data['thread_id'], thread.pk)
        self.assertEqual(data['result']['response'], 'Bio-Fuel is a degreaser.')
        self.assertEqual(response['X-AI-Thread-Id'], str(thread.pk))

    def test_follow_up_appends_only_last_user_message(self):
        thread = AIThread.objects.create(user=self.user, kind='question', title='What is Bio-Fuel?')
        AIMessage.objects.create(thread=thread, role='user', content='What is Bio-Fuel?')
        AIMessage.objects.create(thread=thread, role='assistant', content='A degreaser.')

        history = [
            {'role': 'user', 'content': 'What is Bio-Fuel?'},
            {'role': 'assistant', 'content': 'A degreaser.'},
            {'role': 'user', 'content': 'What dilution?'},
        ]
        upstream = json_upstream({'text': '20ml per litre.'})
        with patch('ai.views.requests.request', return_value=upstream):
            response = self.post_json(REPLY_PATH, {'messages': history},
                                      HTTP_X_AI_THREAD_ID=str(thread.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AIThread.objects.count(), 1)
        messages = list(thread.messages.all())
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[2].role, 'user')
        self.assertEqual(messages[2].content, 'What dilution?')
        self.assertEqual(messages[3].role, 'assistant')
        self.assertEqual(messages[3].content, '20ml per litre.')
        self.assertEqual(json.loads(response.content)['thread_id'], thread.pk)

    def test_foreign_thread_id_creates_new_thread(self):
        foreign = AIThread.objects.create(user=self.other_user, kind='question', title='theirs')

        upstream = json_upstream({'text': 'Answer.'})
        with patch('ai.views.requests.request', return_value=upstream):
            response = self.post_json(REPLY_PATH, {'messages': [{'role': 'user', 'content': 'Hi'}]},
                                      HTTP_X_AI_THREAD_ID=str(foreign.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(foreign.messages.count(), 0)
        new_thread = AIThread.objects.get(user=self.user)
        self.assertNotEqual(new_thread.pk, foreign.pk)
        self.assertEqual(json.loads(response.content)['thread_id'], new_thread.pk)

    def test_competitor_image_not_stored(self):
        image_b64 = base64.b64encode(b'fake-jpeg-bytes' * 100).decode('ascii')
        payload = {'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': 'Compare this to Geller products'},
            {'type': 'image', 'image': image_b64, 'mediaType': 'image/jpeg'},
        ]}]}
        upstream = json_upstream({'text': 'That is Diversey X; use OneDose SC2.'})
        with patch('ai.views.requests.request', return_value=upstream):
            response = self.post_json(COMPETITOR_PATH, payload)

        self.assertEqual(response.status_code, 200)
        thread = AIThread.objects.get()
        self.assertEqual(thread.kind, 'competitor')
        user_message = thread.messages.get(role='user')
        self.assertEqual(user_message.content, 'Compare this to Geller products')
        self.assertTrue(user_message.metadata['has_image'])
        self.assertEqual(user_message.metadata['image_media_type'], 'image/jpeg')
        self.assertNotIn(image_b64, user_message.content)
        self.assertNotIn(image_b64, json.dumps(user_message.metadata))

    def test_non_json_upstream_body_relayed_verbatim(self):
        upstream = FakeUpstreamResponse(status_code=200, body=b'not json', content_type='text/plain')
        with patch('ai.views.requests.request', return_value=upstream):
            response = self.post_json(WORKFLOW_PATH, {'inputData': {'question': 'Hello?'}})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'not json')
        # Capture still recorded the user side; thread id travels in the header.
        thread = AIThread.objects.get()
        self.assertEqual(thread.messages.count(), 1)
        self.assertEqual(response['X-AI-Thread-Id'], str(thread.pk))

    def test_timeout_returns_504_and_persists_user_message(self):
        with patch('ai.views.requests.request', side_effect=requests.Timeout):
            response = self.post_json(WORKFLOW_PATH, {'inputData': {'question': 'Slow one'}})

        self.assertEqual(response.status_code, 504)
        self.assertEqual(json.loads(response.content), {'error': 'AI service timed out'})
        message = AIThread.objects.get().messages.get()
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.metadata['upstream_status'], 504)

    def test_connection_error_returns_502(self):
        with patch('ai.views.requests.request', side_effect=requests.ConnectionError):
            response = self.post_json(REPLY_PATH, {'messages': [{'role': 'user', 'content': 'Hi'}]})

        self.assertEqual(response.status_code, 502)
        self.assertEqual(json.loads(response.content), {'error': 'AI service unavailable'})
        message = AIThread.objects.get().messages.get()
        self.assertEqual(message.metadata['upstream_status'], 502)

    def test_admin_thread_pages_render(self):
        thread = AIThread.objects.create(user=self.user, kind='question', title='What is Bio-Fuel?')
        AIMessage.objects.create(thread=thread, role='user', content='What is Bio-Fuel?',
                                 metadata={'upstream_status': 200})
        AIMessage.objects.create(
            thread=thread, role='assistant', content='A **degreaser** <with markup>.',
            metadata={'upstream_status': 200, 'usage': {'input_tokens': 10, 'output_tokens': 5}})

        admin_user = User.objects.create_superuser('admin2', 'admin2@example.com', 'pw')
        self.client.force_login(admin_user)

        response = self.client.get('/admin/ai/aithread/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/admin/ai/aithread/{}/change/'.format(thread.pk))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('GellerIQ', content)
        self.assertIn('10/5 tokens in/out', content)
        # Message markup must arrive escaped, not raw.
        self.assertIn('&lt;with markup&gt;', content)

    def test_upstream_error_status_passed_through(self):
        upstream = json_upstream({'error': 'invalid token'}, status_code=401)
        with patch('ai.views.requests.request', return_value=upstream):
            response = self.post_json(WORKFLOW_PATH, {'inputData': {'question': 'Q'}})

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'invalid token')
        # User message recorded with the failure status; no assistant message.
        thread = AIThread.objects.get()
        self.assertEqual([m.role for m in thread.messages.all()], ['user'])
        self.assertEqual(thread.messages.get().metadata['upstream_status'], 401)
