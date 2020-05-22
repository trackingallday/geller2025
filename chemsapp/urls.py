from django.contrib import admin
from django.conf.urls import url
from rest_framework.authtoken import views as drf_views
from chemsapp.views import index, customers_list, products_list, new_customer, edit_customer, safety_wears_list,\
    new_product, edit_product, user_details, products_map, customers_table, customers_table_admin, distributors_list,\
    new_distributor, edit_distributor, printout, public_products, markets_list, marketing_site, categories_list, create_contact,\
    sizes_list, download_product_document

urlpatterns = [
    url(r'^auth$', drf_views.obtain_auth_token, name='auth'),

    # Marketing utility routes
    url(r'^product_download/(?P<product_id>\d+)/(?P<document_type>[a-z]{3,4})/$', download_product_document, name="product_download"),

    # Safety frontend
    url(r'^app/$', index, name='index'),
    url(r'^customers/$', index, name='index'),
    url(r'^products/$', index, name='index'),
    url(r'^distributors/$', index, name='index'),
    url(r'^maps/$', index, name='index'),
    url(r'^customer_sheet/', index, name='index'),

    # API, the URLs are not closed with $
    url(r'^customers_list/', customers_list, name='customers_list'),
    url(r'^list_products/', products_list, name='products_list'),
    url(r'^distributors_list/', distributors_list, name='distributors_list'),
    url(r'^new_customer/', new_customer, name="new_customer"),
    url(r'^edit_customer/', edit_customer, name="edit_customer"),
    url(r'^safety_wears_list', safety_wears_list, name="safety_wears_list"),
    url(r'^new_distributor/', new_distributor, name="new_distributor"),
    url(r'^edit_distributor/', edit_distributor, name="edit_distributor"),
    url(r'^new_product/', new_product, name="new_product"),
    url(r'^edit_product/', edit_product, name="edit_product"),
    url(r'^user_details/', user_details, name="user_details"),
    url(r'^list_products_map/', products_map, name="products_map"),
    url(r'^customers_table_admin/', customers_table_admin, name="customers_table_admin"),
    url(r'^customers_table/', customers_table, name="customers_table"),
    url(r'^printout/', printout, name="printout"),
    url(r'^public_products/', public_products, name="public_products"),
    url(r'^create_contact/', create_contact, name="create_contact"),
    url(r'^markets_list/', markets_list, name="markets_list"),
    url(r'^categories_list/', categories_list, name="categories_list"),
    url(r'^sizes_list/', sizes_list, name="sizes_list"),

    # Marketing frontend
    url(r'^$', marketing_site, name='marketing_site'),
    # Product List
    url(r'^our_products/(?:all|\d+)/$', marketing_site, name='marketing_our_products'),
    url(r'^our_products/(?:all|\d+)/\d+/$', marketing_site, name='marketing_our_products_sub_category'),
    # Product
    url(r'^product/\d+/$', marketing_site, name='marketing_site_product'),
    url(r'^product/\d+/\d+/$', marketing_site, name='marketing_site_product_market_id'),
    # Market List and Market
    url(r'^our_markets/$', marketing_site, name='marketing_site_our_markets'),
    url(r'^our_markets/\d+/$', marketing_site, name='marketing_site_our_markets_market_id'),
    # About page and posts
    url(r'^about/$', marketing_site, name='marketing_site_about'),
    url(r'^about/\d+/$', marketing_site, name='marketing_site_about_post'),
    # News page and posts
    url(r'^news/$', marketing_site, name='marketing_site_news'),
    url(r'^news/\d+/$', marketing_site, name='marketing_site_news_post'),
    # Support page and posts
    url(r'^support/$', marketing_site, name='marketing_site_support'),
    url(r'^support/\d+/$', marketing_site, name='marketing_site_support_post'),
    # Contact page and inquiry
    url(r'^contact/$', marketing_site, name='marketing_site_contact'),
    url(r'^contact/.+$', marketing_site, name='marketing_site_contact_message'),
    # Any unmatched route will 404 and it'll drop down to handler404 below.
]

def handler404(request):
    # Render the marketing site app (React) but change the status code.
    # This lets us handle the 404 client side, but without breaking
    # HTTP protocol.
    response = marketing_site(request)
    response.status_code = 404
    return response