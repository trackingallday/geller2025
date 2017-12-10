from django.contrib import admin
from django.conf.urls import url
from rest_framework.authtoken import views as drf_views
from chemsapp.views import index, customers_list, products_list, new_customer

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^auth$', drf_views.obtain_auth_token, name='auth'),
    url(r'^$', index, name='index'),
    url(r'^customers_list/', customers_list, name='customers_list'),
    url(r'^products_list/', products_list, name='products_list'),
    url(r'^new_customer/', new_customer, name="new_customer"),
]
