import json
import logging

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ai.capture import capture_exchange, is_capture_route

logger = logging.getLogger(__name__)

# Only these request headers reach the AI service. Host/Content-Length are
# recomputed by requests; X-AI-Thread-Id is Django-internal.
FORWARD_REQUEST_HEADERS = ('Authorization', 'Content-Type', 'Accept')


class AIProxyView(APIView):
    """Catch-all proxy: /ai/<subpath> → GELLER_AI_ENDPOINT/<subpath>.

    Django authenticates with its own token auth, then forwards the request
    body verbatim (Mastra validates payload shapes, so it must arrive
    byte-identical) along with the Authorization header — geller_ai's own
    token check against this server keeps working unchanged. Known chat
    endpoints additionally get their exchanges persisted via ai.capture.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = []  # never let DRF consume/parse the body

    def get(self, request, subpath):
        return self._proxy(request, subpath)

    def post(self, request, subpath):
        return self._proxy(request, subpath)

    def put(self, request, subpath):
        return self._proxy(request, subpath)

    def patch(self, request, subpath):
        return self._proxy(request, subpath)

    def delete(self, request, subpath):
        return self._proxy(request, subpath)

    def _proxy(self, request, subpath):
        url = settings.GELLER_AI_ENDPOINT.rstrip('/') + '/' + subpath.lstrip('/')
        query = request.META.get('QUERY_STRING')
        if query:
            url += '?' + query

        headers = {}
        for name in FORWARD_REQUEST_HEADERS:
            value = request.headers.get(name)
            if value:
                headers[name] = value

        body = request.body
        capture = is_capture_route(request.method, subpath)

        try:
            upstream = requests.request(
                request.method,
                url,
                data=body or None,
                headers=headers,
                timeout=settings.GELLER_AI_TIMEOUT,
                # Capture routes must be buffered so the JSON can be read;
                # everything else streams through untouched (also covers the
                # Mastra SSE endpoints if the app ever adopts them).
                stream=not capture,
            )
        except requests.Timeout:
            logger.warning('AI proxy: upstream timed out for %s', subpath)
            if capture:
                self._safe_capture(request, subpath, body, 504, None)
            return JsonResponse({'error': 'AI service timed out'}, status=504)
        except requests.RequestException:
            logger.exception('AI proxy: upstream request failed for %s', subpath)
            if capture:
                self._safe_capture(request, subpath, body, 502, None)
            return JsonResponse({'error': 'AI service unavailable'}, status=502)

        content_type = upstream.headers.get('Content-Type', 'application/json')

        if not capture:
            return StreamingHttpResponse(
                upstream.iter_content(8192),
                status=upstream.status_code,
                content_type=content_type,
            )

        upstream_body = upstream.content
        thread = self._safe_capture(request, subpath, body, upstream.status_code, upstream_body)

        response_body = upstream_body
        if thread is not None:
            # Tell the client which thread this exchange landed in; it sends
            # the id back via X-AI-Thread-Id on follow-ups. Non-JSON bodies
            # pass through untouched (the response header still carries it).
            try:
                data = json.loads(upstream_body.decode('utf-8'))
                if isinstance(data, dict):
                    data['thread_id'] = thread.pk
                    response_body = json.dumps(data).encode('utf-8')
            except (ValueError, UnicodeDecodeError):
                pass

        response = HttpResponse(response_body, status=upstream.status_code, content_type=content_type)
        if thread is not None:
            response['X-AI-Thread-Id'] = str(thread.pk)
        return response

    def _safe_capture(self, request, subpath, request_body, upstream_status, upstream_body):
        try:
            return capture_exchange(request, subpath, request_body, upstream_status, upstream_body)
        except Exception:
            logger.exception('AI capture failed for %s', subpath)
            return None
