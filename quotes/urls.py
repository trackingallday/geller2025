from django.urls import path
from . import views, dashboard_views

app_name = 'quotes'

urlpatterns = [
    # API (token auth, consumed by the app)
    path('catalogue/', views.quote_catalogue, name='quote_catalogue'),
    path('submit/', views.submit_quote, name='submit_quote'),
    path('email-pdf/', views.email_quote_pdf, name='email_quote_pdf'),
    # Dashboard (session auth, admin-facing test pages)
    path('dashboard/', dashboard_views.quote_dashboard, name='quote_dashboard'),
    path('dashboard/create/', dashboard_views.dashboard_create_quote, name='dashboard_create_quote'),
    path('dashboard/<int:quote_id>/email/', dashboard_views.dashboard_email_quote, name='dashboard_email_quote'),
    path('<int:pk>/', views.quote_detail, name='quote_detail'),
    path('', views.quotes_list, name='quotes_list'),
]
