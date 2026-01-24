from django.urls import path
from . import views, views_builder, api_views, completed_reports

app_name = 'reports'

urlpatterns = [
    # Report Type Management
    path('', views.report_type_list, name='report_type_list'),
    path('create/', views.report_type_create, name='report_type_create'),
    path('<int:pk>/', views.report_type_detail, name='report_type_detail'),
    path('<int:pk>/edit/', views.report_type_edit, name='report_type_edit'),
    path('<int:pk>/delete/', views.report_type_delete, name='report_type_delete'),
    path('<int:pk>/duplicate/', views.report_type_duplicate, name='report_type_duplicate'),
    
    # Enhanced Form Builder
    path('builder/wizard/', views_builder.report_builder_wizard, name='report_builder_wizard'),
    path('builder/<int:report_type_id>/', views_builder.form_builder, name='form_builder'),
    path('builder/<int:report_type_id>/customers/', views_builder.customer_assignments, name='customer_assignments'),
    path('builder/<int:report_type_id>/rules/', views_builder.conditional_rules, name='conditional_rules'),
    
    # AJAX Endpoints for Builder
    path('ajax/<int:report_type_id>/section/create/', views_builder.ajax_create_section, name='ajax_create_section'),
    path('ajax/<int:report_type_id>/question/create/', views_builder.ajax_create_question, name='ajax_create_question'),
    path('ajax/<int:report_type_id>/template/create/', views_builder.ajax_create_from_template, name='ajax_create_from_template'),
    path('ajax/<int:report_type_id>/order/update/', views_builder.ajax_update_order, name='ajax_update_order'),
    path('ajax/<int:report_type_id>/delete/', views_builder.ajax_delete_item, name='ajax_delete_item'),
    path('ajax/question/<int:question_id>/options/', views.get_question_options_ajax, name='ajax_get_question_options'),
    
    # Templates Management
    path('templates/', views_builder.question_templates, name='question_templates'),
    
    # Section Management
    path('<int:report_type_id>/sections/create/', views.section_create, name='section_create'),
    path('sections/<int:pk>/edit/', views.section_edit, name='section_edit'),
    path('sections/<int:pk>/delete/', views.section_delete, name='section_delete'),
    path('sections/<int:pk>/duplicate/', views.section_duplicate, name='section_duplicate'),
    
    # Question Management
    path('<int:report_type_id>/questions/create/', views.question_create, name='question_create'),
    path('questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
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
    path('api/user/profile/', api_views.get_user_profile_api, name='api_user_profile'),
    path('api/email-report-pdf/', api_views.email_report_pdf, name='api_email_report_pdf'),
]