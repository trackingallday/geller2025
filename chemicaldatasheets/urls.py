"""chemicaldatasheets URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  re_path(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  re_path(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  re_path(r'^blog/', include('blog.urls'))
"""
from django.urls import re_path

from django.contrib import admin
from django.conf.urls import include
from rest_framework.authtoken import views as rest_framework_views
from chemsapp.auth_views import CustomAuthToken
from django.conf import settings
from django.views.static import serve
from django.views.generic.base import RedirectView
from chemsapp.views import upload_file



urlpatterns = [
    re_path(r'^$', RedirectView.as_view(url='/admin/', permanent=True), name='home'),
    re_path(r'^admin/', admin.site.urls, name='admin'),
    re_path(r'^admin$', RedirectView.as_view(url='/admin/', permanent=True)),
    re_path(r'^get_auth_token/$', CustomAuthToken.as_view(), name='get_auth_token'),
    re_path(r'^accounts/', include('django.contrib.auth.urls')),
    re_path(r'^upload_file/', upload_file, name='upload_file'),
    re_path(r'^reports/', include('reports.urls')),
    re_path(r'^orders/', include('orders.urls')),
    re_path(r'^tickets/', include('tickets.urls')),
    re_path(r'', include('chemsapp.urls' )),

]

# Serve user-uploaded media. Django's static() helper no-ops when DEBUG=False,
# and WhiteNoise only indexes files present at startup (media is uploaded at
# runtime to the /data volume), so wire the serve view directly for all modes.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
