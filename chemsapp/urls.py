from django.contrib import admin
from django.conf.urls import url
from rest_framework.authtoken import views as drf_views
from chemsapp.views import index, customers_list, products_list, new_customer, edit_customer, safety_wears_list,\
    new_product, edit_product, user_details, products_map, customers_table, customers_table_admin, distributors_list,\
    new_distributor, edit_distributor, customer_sheet

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^auth$', drf_views.obtain_auth_token, name='auth'),
    url(r'^$', index, name='index'),
    url(r'^customers$', index, name='index'),
    url(r'^products$', index, name='index'),
    url(r'^maps$', index, name='index'),
    url(r'^customers_list/', customers_list, name='customers_list'),
    url(r'^products_list/', products_list, name='products_list'),
    url(r'^distributors_list/', distributors_list, name='distributors_list'),
    url(r'^new_customer/', new_customer, name="new_customer"),
    url(r'^edit_customer/', edit_customer, name="edit_customer"),
    url(r'^safety_wears_list', safety_wears_list, name="safety_wears_list"),
    url(r'^new_/', new_product, name="new_product"),
    url(r'^new_distributor/', new_distributor, name="new_distributor"),
    url(r'^edit_distributor/', edit_distributor, name="edit_distributor"),
    url(r'^new_product/', new_product, name="new_product"),
    url(r'^edit_product/', edit_product, name="edit_product"),
    url(r'^user_details/', user_details, name="user_details"),
    url(r'^products_map/', products_map, name="products_map"),
    url(r'^customers_table_admin/', customers_table_admin, name="customers_table_admin"),
    url(r'^customers_table/', customers_table, name="customers_table"),
    url(r'^customer_sheet/', customer_sheet, name="customer_sheet"),
]
