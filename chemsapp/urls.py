from django.contrib import admin
from django.urls import re_path
from rest_framework.authtoken import views as drf_views
from chemsapp.views import customers_list, products_list, new_customer, edit_customer, safety_wears_list,\
    new_product, edit_product, user_details, products_map, customers_table, customers_table_admin, distributors_list,\
    new_distributor, edit_distributor, printout, public_products, markets_list, categories_list, create_contact,\
    sizes_list, download_product_document, sds_enquire, special_customer_edit

urlpatterns = [
    re_path(r'^auth$', drf_views.obtain_auth_token, name='auth'),

    # Marketing utility routes
    re_path(r'^product_download/(?P<product_id>\d+)/(?P<document_type>[a-z]{3,4})/$', download_product_document, name="product_download"),

    # API, the URLs are not closed with $
    re_path(r'^customers_list/', customers_list, name='customers_list'),
    re_path(r'^list_products/', products_list, name='products_list'),
    re_path(r'^distributors_list/', distributors_list, name='distributors_list'),
    re_path(r'^new_customer/', new_customer, name="new_customer"),
    re_path(r'^edit_customer/', edit_customer, name="edit_customer"),
    re_path(r'^special_customer_edit/', special_customer_edit, name="special_customer_edit"),
    re_path(r'^safety_wears_list', safety_wears_list, name="safety_wears_list"),
    re_path(r'^new_distributor/', new_distributor, name="new_distributor"),
    re_path(r'^edit_distributor/', edit_distributor, name="edit_distributor"),
    re_path(r'^new_product/', new_product, name="new_product"),
    re_path(r'^edit_product/', edit_product, name="edit_product"),
    re_path(r'^user_details/', user_details, name="user_details"),
    re_path(r'^list_products_map/', products_map, name="products_map"),
    re_path(r'^customers_table_admin/', customers_table_admin, name="customers_table_admin"),
    re_path(r'^customers_table/', customers_table, name="customers_table"),
    re_path(r'^printout/', printout, name="printout"),
    re_path(r'^public_products/', public_products, name="public_products"),
    re_path(r'^create_contact/', create_contact, name="create_contact"),
    re_path(r'^markets_list/', markets_list, name="markets_list"),
    re_path(r'^categories_list/', categories_list, name="categories_list"),
    re_path(r'^sizes_list/', sizes_list, name="sizes_list"),
    re_path(r'^sds_enquire/', sds_enquire, name="sds_enquire"),

   
]
