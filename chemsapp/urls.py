from django.contrib import admin
from django.urls import re_path
from rest_framework.authtoken import views as drf_views
from chemsapp.views import customers_list, products_list, sds_products, info_sheet_products, new_customer, edit_customer, safety_wears_list,\
    new_product, edit_product, user_details, products_map, customers_table, customers_table_admin, distributors_list,\
    new_distributor, edit_distributor, printout, public_products, markets_list, categories_list, create_contact,\
    sizes_list, download_product_document, sds_enquire, special_customer_edit, backup_documents
from chemsapp.wall_chart_views import wall_chart_pdf
from chemsapp import product_dashboard_views
from chemsapp import customer_dashboard_views

urlpatterns = [
    re_path(r'^auth$', drf_views.obtain_auth_token, name='auth'),

    # Product dashboard (staff only, session auth)
    re_path(r'^product-dashboard/$', product_dashboard_views.product_dashboard,
            name='product_dashboard'),
    re_path(r'^product-dashboard/(?P<product_id>\d+)/save-details/$',
            product_dashboard_views.save_product_details, name='save_product_details'),
    re_path(r'^product-dashboard/(?P<product_id>\d+)/save-compliance/$',
            product_dashboard_views.save_product_compliance, name='save_product_compliance'),
    re_path(r'^product-dashboard/(?P<product_id>\d+)/save-variants/$',
            product_dashboard_views.save_variants, name='save_variants'),
    re_path(r'^product-dashboard/(?P<product_id>\d+)/save-equivalents/$',
            product_dashboard_views.save_equivalents, name='save_equivalents'),
    re_path(r'^product-dashboard/(?P<product_id>\d+)/add-customer/$',
            product_dashboard_views.add_product_customer, name='add_product_customer'),
    re_path(r'^product-dashboard/(?P<product_id>\d+)/remove-customer/(?P<customer_id>\d+)/$',
            product_dashboard_views.remove_product_customer, name='remove_product_customer'),
    re_path(r'^product-dashboard/customer-search/$',
            product_dashboard_views.customer_search, name='dashboard_customer_search'),
    re_path(r'^product-dashboard/category-search/$',
            product_dashboard_views.category_search, name='dashboard_category_search'),
    re_path(r'^product-dashboard/product-list/$',
            product_dashboard_views.product_list, name='dashboard_product_list'),
    re_path(r'^product-dashboard/variant/(?P<variant_id>\d+)/save-dilutions/$',
            product_dashboard_views.save_dilutions, name='save_dilutions'),
    re_path(r'^product-dashboard/variant/(?P<variant_id>\d+)/save/$',
            product_dashboard_views.save_one_variant, name='save_one_variant'),
    re_path(r'^product-dashboard/variant/(?P<variant_id>\d+)/delete/$',
            product_dashboard_views.delete_variant, name='delete_variant'),
    re_path(r'^product-dashboard/(?P<product_id>\d+)/add-variant/$',
            product_dashboard_views.create_variant, name='create_variant'),
    re_path(r'^product-dashboard/variant/(?P<variant_id>\d+)/save-price/$',
            product_dashboard_views.save_pricing_variant, name='save_pricing_variant'),
    re_path(r'^product-dashboard/price/(?P<pricing_variant_id>\d+)/delete/$',
            product_dashboard_views.delete_pricing_variant, name='delete_pricing_variant'),
    re_path(r'^product-dashboard/variant/(?P<variant_id>\d+)/save-group-price/$',
            product_dashboard_views.save_group_pricing_variant,
            name='save_group_pricing_variant'),
    re_path(r'^product-dashboard/group-price/(?P<group_pricing_variant_id>\d+)/delete/$',
            product_dashboard_views.delete_group_pricing_variant,
            name='delete_group_pricing_variant'),

    # Customer dashboard (staff only, session auth)
    re_path(r'^customer-dashboard/$', customer_dashboard_views.customer_dashboard,
            name='customer_dashboard'),
    re_path(r'^customer-dashboard/(?P<customer_id>\d+)/save-details/$',
            customer_dashboard_views.save_customer_details, name='save_customer_details'),
    re_path(r'^customer-dashboard/(?P<customer_id>\d+)/save-contacts/$',
            customer_dashboard_views.save_customer_contacts, name='save_customer_contacts'),
    re_path(r'^customer-dashboard/(?P<customer_id>\d+)/set-group/$',
            customer_dashboard_views.set_customer_group, name='set_customer_group'),
    re_path(r'^customer-dashboard/customer-list/$',
            customer_dashboard_views.customer_list, name='dashboard_customer_list'),
    re_path(r'^customer-dashboard/group-list/$',
            customer_dashboard_views.group_list, name='dashboard_group_list'),
    re_path(r'^customer-dashboard/group-customer-search/$',
            customer_dashboard_views.group_customer_search, name='dashboard_group_customer_search'),
    re_path(r'^customer-dashboard/variant-search/$',
            customer_dashboard_views.variant_search, name='dashboard_variant_search'),
    re_path(r'^customer-dashboard/group/(?P<group_id>\d+)/add-price/$',
            customer_dashboard_views.add_group_price, name='add_group_price'),
    re_path(r'^customer-dashboard/group/(?P<group_id>\d+)/remove-price/(?P<group_pricing_variant_id>\d+)/$',
            customer_dashboard_views.remove_group_price, name='remove_group_price'),
    re_path(r'^customer-dashboard/create-group/$',
            customer_dashboard_views.create_group, name='create_customer_group'),
    re_path(r'^customer-dashboard/group/(?P<group_id>\d+)/rename/$',
            customer_dashboard_views.rename_group, name='rename_group'),
    re_path(r'^customer-dashboard/group/(?P<group_id>\d+)/delete/$',
            customer_dashboard_views.delete_group, name='delete_group'),
    re_path(r'^customer-dashboard/group/(?P<group_id>\d+)/add-customers/$',
            customer_dashboard_views.add_group_customers, name='add_group_customers'),
    re_path(r'^customer-dashboard/group/(?P<group_id>\d+)/remove-customer/(?P<customer_id>\d+)/$',
            customer_dashboard_views.remove_group_customer, name='remove_group_customer'),

    # Marketing utility routes
    re_path(r'^product_download/(?P<product_id>\d+)/(?P<document_type>[a-z]{3,4})/$', download_product_document, name="product_download"),

    # API, the URLs are not closed with $
    re_path(r'^customers_list/', customers_list, name='customers_list'),
    re_path(r'^list_products/', products_list, name='products_list'),
    re_path(r'^sds_products/', sds_products, name='sds_products'),
    re_path(r'^info_sheet_products/', info_sheet_products, name='info_sheet_products'),
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
    re_path(r'^backup_documents/', backup_documents, name="backup_documents"),
    re_path(r'^wall_chart_pdf/', wall_chart_pdf, name="wall_chart_pdf"),


]
