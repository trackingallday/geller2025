from django.urls import re_path

from ai.views import AIProxyView

urlpatterns = [
    re_path(r'^(?P<subpath>.*)$', AIProxyView.as_view(), name='ai-proxy'),
]
