"""Staff gate and JSON helpers shared by the dashboard views.

The dashboards began as server-rendered pages behind
``@staff_member_required``, which answers an unauthenticated request with a
redirect to the admin login page. A single-page app on another origin cannot
use that: it needs a status code and a JSON body, and it carries a DRF token
rather than a session cookie.

``staff_api`` replaces that decorator. It accepts either credential, so the
old templates keep working while the new app is built against the same views.
"""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from functools import wraps
from rest_framework.authtoken.models import Token


def _user_from_token(request):
    """The user behind an ``Authorization: Token <key>`` header, or None.

    A malformed header is not an error here: it simply yields no user, and
    the caller falls back to the session before deciding to refuse.
    """
    header = request.META.get('HTTP_AUTHORIZATION', '')
    if not header.startswith('Token '):
        return None
    key = header[len('Token '):].strip()
    if not key:
        return None
    try:
        return Token.objects.select_related('user').get(key=key).user
    except Token.DoesNotExist:
        return None


def wants_json(request):
    """True when the caller asked for JSON rather than a redirect.

    The SPA sets this header on every request. A browser posting one of the
    old forms does not, so the same view keeps redirecting for them.
    """
    return 'application/json' in request.META.get('HTTP_ACCEPT', '')


def staff_api(view):
    """Allow staff in by token or by session; refuse everyone else in JSON.

    Replaces ``@staff_member_required`` on the dashboard views. The token path
    is CSRF-exempt because a bearer token is not sent automatically by the
    browser, so it cannot be used for cross-site request forgery; the session
    path keeps Django's CSRF protection.
    """
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        token_user = _user_from_token(request)
        if token_user is not None:
            request.user = token_user
        user = getattr(request, 'user', None)

        if user is None or not user.is_authenticated:
            return JsonResponse(
                {'ok': False, 'detail': 'Authentication required.'}, status=401)
        if not user.is_staff:
            return JsonResponse(
                {'ok': False, 'detail': 'Staff access required.'}, status=403)
        if not user.is_active:
            return JsonResponse(
                {'ok': False, 'detail': 'This account is not active.'}, status=403)

        return view(request, *args, **kwargs)

    # Only the token path skips CSRF. A session request still needs its token,
    # which Django enforces inside the view's own middleware chain.
    return csrf_exempt(wrapper)


def json_body(request):
    """The request's JSON body as a dict, or an empty dict.

    The old forms post ``application/x-www-form-urlencoded``; the SPA posts
    JSON. Views that accept both read their fields through this.
    """
    if not request.body:
        return {}
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def form_data(request):
    """The posted fields, whichever content type they arrived in.

    Django forms want a mapping, so a JSON body is handed over as a plain
    dict. Files always come from ``request.FILES``.
    """
    if request.content_type and 'application/json' in request.content_type:
        return json_body(request)
    return request.POST


def ok(data=None, **extra):
    """A success envelope: ``{ok: true, data: ...}``."""
    payload = {'ok': True, 'data': data if data is not None else {}}
    payload.update(extra)
    return JsonResponse(payload)


def form_errors_response(form, status=400):
    """A validation failure, with Django's own per-field error dict."""
    return JsonResponse({'ok': False, 'errors': form.errors}, status=status)


def error(detail, status=400, **extra):
    """A failure that is not a form validation error."""
    payload = {'ok': False, 'detail': detail}
    payload.update(extra)
    return JsonResponse(payload, status=status)
