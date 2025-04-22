from django.contrib import admin
from django.urls import path, re_path
from rest_framework.authtoken import views as drf_views
from chemsapp.views import index, customers_list, products_list, new_customer, edit_customer, safety_wears_list,\
    new_product, edit_product, user_details, products_map, customers_table, customers_table_admin, distributors_list,\
    new_distributor, edit_distributor, printout, public_products, markets_list, marketing_site, categories_list, create_contact,\
    sizes_list, download_product_document, sds_enquire

app_name = 'chemsapp'

urlpatterns = [
    path('auth', drf_views.obtain_auth_token, name='auth'),

    # Marketing utility routes
    re_path(r'^product_download/(?P<product_id>\d+)/(?P<document_type>[a-z]{3,4})/$', download_product_document, name="product_download"),

    # Safety frontend
    path('app/', index, name='index'),
    path('customers/', index, name='index'),
    path('products/', index, name='index'),
    path('distributors/', index, name='index'),
    path('maps/', index, name='index'),
    re_path(r'^customer_sheet/', index, name='index'),

    # API, the URLs are not closed with $
    re_path(r'^customers_list/', customers_list, name='customers_list'),
    re_path(r'^list_products/', products_list, name='products_list'),
    re_path(r'^distributors_list/', distributors_list, name='distributors_list'),
    re_path(r'^new_customer/', new_customer, name="new_customer"),
    re_path(r'^edit_customer/', edit_customer, name="edit_customer"),
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

    # Marketing frontend
    path('', marketing_site, name='marketing_site'),
    # Product List
    re_path(r'^our_products/(?:all|\d+)/$', marketing_site, name='marketing_our_products'),
    re_path(r'^our_products/(?:all|\d+)/\d+/$', marketing_site, name='marketing_our_products_sub_category'),
    # Product
    re_path(r'^product/\d+/$', marketing_site, name='marketing_site_product'),
    re_path(r'^product/\d+/\d+/$', marketing_site, name='marketing_site_product_market_id'),
    # Market List and Market
    path('our_markets/', marketing_site, name='marketing_site_our_markets'),
    re_path(r'^our_markets/\d+/$', marketing_site, name='marketing_site_our_markets_market_id'),
    # About page and posts
    path('about/', marketing_site, name='marketing_site_about'),
    re_path(r'^about/\d+/$', marketing_site, name='marketing_site_about_post'),
    # News page and posts
    path('news/', marketing_site, name='marketing_site_news'),
    re_path(r'^news/\d+/$', marketing_site, name='marketing_site_news_post'),
    # Support page and posts
    path('support/', marketing_site, name='marketing_site_support'),
    re_path(r'^support/\d+/$', marketing_site, name='marketing_site_support_post'),
    # Contact page and inquiry
    path('contact/', marketing_site, name='marketing_site_contact'),
    re_path(r'^contact/\d+/$', marketing_site, name='marketing_site_contact_product_id'),
    # SDS Download page
    re_path(r'^getsds/\d+/$', marketing_site, name='marketing_site_getsds_product_id'),
    # Sectors page and sector detail
    path('sectors/', marketing_site, name='marketing_site_sectors'),
    re_path(r'^sectors/\d+/$', marketing_site, name='marketing_site_sector_detail'),
    # Any unmatched route will 404 and it'll drop down to handler404 below.
]

def handler404(request, exception):
    # Render the marketing site app (React) but change the status code.
    # This lets us handle the 404 client side, but without breaking
    # HTTP protocol.
    response = marketing_site(request)
    response.status_code = 404
    return response