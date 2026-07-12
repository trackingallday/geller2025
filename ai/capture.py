"""Persist AI conversations proxied through AIProxyView.

The proxy forwards requests verbatim to the Mastra service (geller_ai); this
module recognises the chat endpoints the mobile app uses and stores each
exchange as AIThread/AIMessage rows. Capture failures must never break the
proxy — the view wraps every call in try/except.
"""
import json
import logging

from django.db import transaction

from ai.models import AIThread, AIMessage

logger = logging.getLogger(__name__)


def _last_user_message(body):
    for message in reversed(body.get('messages') or []):
        if isinstance(message, dict) and message.get('role') == 'user':
            return message
    return None


def _extract_text_user(body):
    """messages: [{role, content: str}] — replyAgent payloads."""
    message = _last_user_message(body)
    if message and isinstance(message.get('content'), str):
        return message['content'], {}
    return None, {}


def _extract_multimodal_user(body):
    """messages where content may be a parts array (text/image).

    Base64 image data is deliberately not stored — a label photo is megabytes
    of base64 that would bloat the DB and its streamed backups. Only the fact
    an image was sent (and its type/size) is kept in metadata.
    """
    message = _last_user_message(body)
    if not message:
        return None, {}
    content = message.get('content')
    if isinstance(content, str):
        return content, {}
    texts = []
    meta = {}
    if isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get('type') == 'text':
                texts.append(part.get('text') or '')
            elif part.get('type') == 'image':
                image = part.get('image')
                meta['has_image'] = True
                meta['image_media_type'] = part.get('mediaType') or ''
                if isinstance(image, str):
                    meta['image_size_bytes'] = len(image) * 3 // 4
    return '\n'.join(t for t in texts if t), meta


def _extract_workflow_user(body):
    """{inputData: {question}} — question-router workflow payloads."""
    question = (body.get('inputData') or {}).get('question')
    if isinstance(question, str):
        return question, {}
    return None, {}


def _extract_workflow_assistant(data):
    if not isinstance(data, dict):
        return None
    result = data.get('result')
    if isinstance(result, dict) and isinstance(result.get('response'), str):
        return result['response']
    steps = data.get('steps')
    if isinstance(steps, dict):
        output = ((steps.get('combine') or {}).get('output')) or {}
        if isinstance(output, dict) and isinstance(output.get('response'), str):
            return output['response']
    return None


def _extract_agent_assistant(data):
    if isinstance(data, dict) and isinstance(data.get('text'), str):
        return data['text']
    return None


CAPTURE_ROUTES = {
    ('POST', 'api/workflows/question-router/start-async'): {
        'kind': 'question',
        'user': _extract_workflow_user,
        'assistant': _extract_workflow_assistant,
    },
    ('POST', 'api/agents/replyAgent/generate'): {
        'kind': 'reply',
        'user': _extract_text_user,
        'assistant': _extract_agent_assistant,
    },
    ('POST', 'api/agents/competitor-comparison-agent/generate'): {
        'kind': 'competitor',
        'user': _extract_multimodal_user,
        'assistant': _extract_agent_assistant,
    },
}


def is_capture_route(method, subpath):
    return (method.upper(), subpath.strip('/')) in CAPTURE_ROUTES


def capture_exchange(request, subpath, request_body, upstream_status, upstream_body):
    """Store the exchange; returns the AIThread used, or None if not captured.

    The app resends the full message history on every follow-up, so only the
    last user message is stored — earlier turns are already persisted. The
    user message is stored even when upstream failed (upstream_status records
    it); the assistant message only on a 2xx with extractable text.
    """
    route = CAPTURE_ROUTES.get((request.method.upper(), subpath.strip('/')))
    if route is None:
        return None

    try:
        body = json.loads(request_body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        logger.warning('AI capture: request body is not JSON for %s', subpath)
        return None
    if not isinstance(body, dict):
        return None

    user_text, user_meta = route['user'](body)
    if user_text is None and not user_meta:
        logger.warning('AI capture: no user message found for %s', subpath)
        return None

    data = None
    if upstream_body is not None:
        try:
            data = json.loads(upstream_body.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            data = None
    assistant_text = route['assistant'](data)

    thread = None
    header_id = request.headers.get('X-AI-Thread-Id')
    if header_id:
        try:
            # Scoped to the requesting user so a client can never append to
            # someone else's thread; an unknown id just starts a new thread.
            thread = AIThread.objects.filter(pk=int(header_id), user=request.user).first()
        except (TypeError, ValueError):
            thread = None

    base_meta = {'endpoint': subpath, 'upstream_status': upstream_status}
    with transaction.atomic():
        if thread is None:
            thread = AIThread.objects.create(
                user=request.user,
                kind=route['kind'],
                title=(user_text or '')[:255],
            )
        AIMessage.objects.create(
            thread=thread,
            role='user',
            content=user_text or '',
            metadata=dict(base_meta, **user_meta),
        )
        if upstream_status is not None and 200 <= upstream_status < 300 and assistant_text is not None:
            assistant_meta = dict(base_meta)
            if isinstance(data, dict):
                if data.get('usage') is not None:
                    assistant_meta['usage'] = data['usage']
                if data.get('model'):
                    assistant_meta['model'] = data['model']
                if data.get('id'):
                    assistant_meta['run_id'] = data['id']
            AIMessage.objects.create(
                thread=thread,
                role='assistant',
                content=assistant_text,
                metadata=assistant_meta,
            )
    return thread
