from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('customer/<int:customer_id>/', views.orders_by_customer, name='orders_by_customer'),
    path('customer/<int:customer_id>/product-variants/', views.customer_product_variants, name='customer_product_variants'),
    path('submit/', views.submit_order, name='submit_order'),
]
