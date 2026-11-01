from django.urls import path
from . import (
    api_views, builder_api_views, completed_reports, staff_api_views, views,
)

app_name = 'reports'

urlpatterns = [
    # Report Type Management
    path('', views.report_type_list, name='report_type_list'),
    path('create/', views.report_type_create, name='report_type_create'),
    path('<int:pk>/', views.report_type_detail, name='report_type_detail'),
    path('<int:pk>/edit/', views.report_type_edit, name='report_type_edit'),
    path('<int:pk>/delete/', views.report_type_delete, name='report_type_delete'),
    path('<int:pk>/duplicate/', views.report_type_duplicate, name='report_type_duplicate'),

    path('ajax/question/<int:question_id>/options/', views.get_question_options_ajax, name='ajax_get_question_options'),

    # Section Management
    path('<int:report_type_id>/sections/create/', views.section_create, name='section_create'),
    path('sections/<int:pk>/edit/', views.section_edit, name='section_edit'),
    path('sections/<int:pk>/delete/', views.section_delete, name='section_delete'),
    path('sections/<int:pk>/duplicate/', views.section_duplicate, name='section_duplicate'),
    
    # Question Management
    path('<int:report_type_id>/questions/create/', views.question_create, name='question_create'),
    path('questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('questions/<int:pk>/duplicate/', views.question_duplicate, name='question_duplicate'),
    path('questions/<int:pk>/options/', views.question_options, name='question_options'),
    
    # Question Option Management
    path('questions/<int:question_id>/options/create/', views.option_create, name='option_create'),
    path('options/<int:pk>/edit/', views.option_edit, name='option_edit'),
    path('options/<int:pk>/delete/', views.option_delete, name='option_delete'),
    
    # Report Instances
    path('instances/', views.report_list, name='report_list'),
    path('instances/create/<int:report_type_id>/', views.report_create, name='report_create'),
    path('instances/<int:pk>/', views.report_detail, name='report_detail'),
    path('instances/<int:pk>/fill/', views.report_fill, name='report_fill'),
    path('instances/<int:pk>/submit/', views.report_submit, name='report_submit'),
    
    # Sample Data
    path('create-sample/', views.create_sample_grocery_report, name='create_sample_grocery_report'),

    # Completed Reports Views
    path('completed/', completed_reports.completed_reports_list, name='completed_reports_list'),
    path('completed/<int:pk>/', completed_reports.completed_report_detail, name='completed_report_detail'),
    path('completed/<int:pk>/generate-pdf/', completed_reports.generate_pdf_view, name='generate_pdf'),
    path('completed/<int:pk>/view-pdf/', completed_reports.view_pdf, name='view_pdf'),
    path('completed/browse-pdfs/', completed_reports.browse_pdfs, name='browse_pdfs'),

    # API Endpoints
    path('api/reports/', api_views.ReportListAPIView.as_view(), name='api_report_list'),
    path('api/reports/<int:pk>/', api_views.ReportDetailAPIView.as_view(), name='api_report_detail'),
    path('api/reports/<int:report_id>/update/', api_views.update_report_api, name='api_report_update'),
    path('api/reports/<int:report_id>/submit/', api_views.submit_report_api, name='api_report_submit'),
    path('api/report-types/', api_views.ReportTypeListAPIView.as_view(), name='api_report_type_list'),
    path('api/report-types/<int:pk>/', api_views.ReportTypeDetailAPIView.as_view(), name='api_report_type_detail'),
    path('api/report-types/<int:report_type_id>/create/', api_views.create_report_api, name='api_report_create'),
    path('api/report-types/<int:report_type_id>/questions/', api_views.report_questions_api, name='api_report_questions'),
    path('api/customer/<int:customer_id>/', api_views.reports_by_customer, name='api_reports_by_customer'),
    path('api/customer/report_types_by_customer/<int:customer_id>/', api_views.report_types_by_customer, name='api_report_types_by_customer'),
    path('api/user/profile/', api_views.get_user_profile_api, name='api_user_profile'),
    path('api/email-report-pdf/', api_views.email_report_pdf, name='api_email_report_pdf'),

    # The admin app's own reads and PDF actions. Separate from the api/
    # endpoints above, which serve the mobile app and answer to its shapes.
    path('staff-api/reports/', staff_api_views.report_list,
         name='staff_api_report_list'),
    path('staff-api/reports/<int:report_id>/', staff_api_views.report_detail,
         name='staff_api_report_detail'),
    path('staff-api/reports/<int:report_id>/generate-pdf/',
         staff_api_views.generate_pdf, name='staff_api_generate_pdf'),
    path('staff-api/reports/<int:report_id>/pdf/', staff_api_views.download_pdf,
         name='staff_api_download_pdf'),
    path('staff-api/report-types/', staff_api_views.report_types,
         name='staff_api_report_types'),

    # The report-type builder for the admin app. Every write answers with
    # the whole builder tree, so the screen redraws from one source.
    path('staff-api/builder/meta/', builder_api_views.builder_meta,
         name='staff_api_builder_meta'),
    path('staff-api/report-types/create/', builder_api_views.report_type_create,
         name='staff_api_report_type_create'),
    path('staff-api/report-types/<int:report_type_id>/', builder_api_views.report_type_tree,
         name='staff_api_report_type_tree'),
    path('staff-api/report-types/<int:report_type_id>/update/',
         builder_api_views.report_type_update, name='staff_api_report_type_update'),
    path('staff-api/report-types/<int:report_type_id>/delete/',
         builder_api_views.report_type_delete, name='staff_api_report_type_delete'),
    path('staff-api/report-types/<int:report_type_id>/duplicate/',
         builder_api_views.report_type_duplicate, name='staff_api_report_type_duplicate'),
    path('staff-api/report-types/<int:report_type_id>/reorder/',
         builder_api_views.report_type_reorder, name='staff_api_report_type_reorder'),
    path('staff-api/report-types/<int:report_type_id>/sections/create/',
         builder_api_views.section_create, name='staff_api_section_create'),
    path('staff-api/report-types/<int:report_type_id>/questions/create/',
         builder_api_views.question_create, name='staff_api_question_create'),
    path('staff-api/report-types/<int:report_type_id>/assignments/',
         builder_api_views.report_type_assignments, name='staff_api_report_type_assignments'),
    path('staff-api/report-types/<int:report_type_id>/assignments/set/',
         builder_api_views.report_type_assignment_set,
         name='staff_api_report_type_assignment_set'),
    path('staff-api/sections/<int:section_id>/update/',
         builder_api_views.section_update, name='staff_api_section_update'),
    path('staff-api/sections/<int:section_id>/delete/',
         builder_api_views.section_delete, name='staff_api_section_delete'),
    path('staff-api/sections/<int:section_id>/duplicate/',
         builder_api_views.section_duplicate, name='staff_api_section_duplicate'),
    path('staff-api/questions/<int:question_id>/update/',
         builder_api_views.question_update, name='staff_api_question_update'),
    path('staff-api/questions/<int:question_id>/delete/',
         builder_api_views.question_delete, name='staff_api_question_delete'),
    path('staff-api/questions/<int:question_id>/duplicate/',
         builder_api_views.question_duplicate, name='staff_api_question_duplicate'),
    path('staff-api/questions/<int:question_id>/options/create/',
         builder_api_views.option_create, name='staff_api_option_create'),
    path('staff-api/questions/<int:question_id>/options/reorder/',
         builder_api_views.option_reorder, name='staff_api_option_reorder'),
    path('staff-api/options/<int:option_id>/update/',
         builder_api_views.option_update, name='staff_api_option_update'),
    path('staff-api/options/<int:option_id>/delete/',
         builder_api_views.option_delete, name='staff_api_option_delete'),
    path('staff-api/assignments/', builder_api_views.assignment_matrix,
         name='staff_api_assignment_matrix'),
    path('staff-api/assignments/toggle/', builder_api_views.assignment_toggle,
         name='staff_api_assignment_toggle'),
]