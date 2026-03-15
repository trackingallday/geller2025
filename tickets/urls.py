from django.urls import path
from . import views, dashboard_views

app_name = 'tickets'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('<int:ticket_id>/update/', views.ticket_update, name='ticket_update'),
    path('<int:ticket_id>/reply/', views.ticket_reply, name='ticket_reply'),
    path('<int:ticket_id>/images/', views.ticket_upload_image, name='ticket_upload_image'),
    # Dashboard
    path('dashboard/', dashboard_views.ticket_dashboard, name='ticket_dashboard'),
    path('dashboard/create/', dashboard_views.dashboard_create_ticket, name='dashboard_create_ticket'),
    path('dashboard/<int:ticket_id>/reply/', dashboard_views.dashboard_reply, name='dashboard_reply'),
    path('dashboard/<int:ticket_id>/status/', dashboard_views.dashboard_update_status, name='dashboard_update_status'),
    path('dashboard/<int:ticket_id>/image/', dashboard_views.dashboard_upload_image, name='dashboard_upload_image'),
    # AJAX helpers for create modal
    path('dashboard/ajax/distributors/', dashboard_views.ajax_distributors_for_customer, name='ajax_distributors_for_customer'),
    path('dashboard/ajax/users/', dashboard_views.ajax_users_for_distributor, name='ajax_users_for_distributor'),
    path('dashboard/<int:ticket_id>/poll/', dashboard_views.ajax_poll_ticket, name='ajax_poll_ticket'),
]
