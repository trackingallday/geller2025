from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from chemsapp.models import Customer
import json

from .models import (
    ReportType, ReportSection, Question, QuestionOption, 
    Report, ReportTypeCustomer, QuestionTemplate
)


class BasicModelTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.report_type = ReportType.objects.create(
            name='Test Report Type',
            description='A test report type',
            created_by=self.user
        )
        
        # Create a customer user and customer profile
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='customerpass123'
        )
        self.customer = Customer.objects.create(
            user=self.customer_user,
            businessName='Test Business',
            phoneNumber='555-1234'
        )

    def test_report_type_creation(self):
        """Test basic ReportType model creation"""
        self.assertEqual(self.report_type.name, 'Test Report Type')
        self.assertEqual(self.report_type.created_by, self.user)
        self.assertTrue(self.report_type.is_active)

    def test_report_type_customer_model(self):
        """Test ReportTypeCustomer model"""
        assignment = ReportTypeCustomer.objects.create(
            report_type=self.report_type,
            customer=self.customer,
            assigned_by=self.user
        )
        
        self.assertEqual(str(assignment), f'{self.report_type.name} -> {self.customer.businessName}')
        self.assertIsNotNone(assignment.assigned_date)
        self.assertTrue(assignment.is_active)

    def test_question_template_model(self):
        """Test QuestionTemplate model"""
        template = QuestionTemplate.objects.create(
            name='Test Template',
            question_text='What is your name?',
            question_type='text',
            category='general',
            created_by=self.user
        )
        
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.usage_count, 0)
        
        # Test increment usage
        template.increment_usage()
        template.refresh_from_db()
        self.assertEqual(template.usage_count, 1)

    def test_question_creation(self):
        """Test Question model creation"""
        question = Question.objects.create(
            report_type=self.report_type,
            question_text='Test Question',
            question_type='text',
            order=1,
            is_required=True
        )
        
        self.assertEqual(question.question_text, 'Test Question')
        self.assertEqual(question.report_type, self.report_type)
        self.assertTrue(question.is_required)


class BasicViewTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.report_type = ReportType.objects.create(
            name='Test Report Type',
            description='A test report type',
            created_by=self.user
        )

    def test_report_type_list_view(self):
        """Test that report type list view works"""
        url = reverse('reports:report_type_list')
        response = self.client.get(url)
        
        # Should work without authentication (or redirect to login)
        self.assertIn(response.status_code, [200, 302])

    def test_report_type_detail_view(self):
        """Test report type detail view"""
        url = reverse('reports:report_type_detail', kwargs={'pk': self.report_type.pk})
        response = self.client.get(url)
        
        # Should work without authentication (or redirect to login)
        self.assertIn(response.status_code, [200, 302])

    def test_form_builder_view_exists(self):
        """Test that form builder view exists"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('reports:form_builder', kwargs={'report_type_id': self.report_type.pk})
        response = self.client.get(url)
        
        # Should either work or redirect, but not 404
        self.assertNotEqual(response.status_code, 404)

    def test_customer_assignments_view_exists(self):
        """Test that customer assignments view exists"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('reports:customer_assignments', kwargs={'report_type_id': self.report_type.pk})
        response = self.client.get(url)
        
        # Should either work or redirect, but not 404
        self.assertNotEqual(response.status_code, 404)


class URLTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.report_type = ReportType.objects.create(
            name='Test Report Type',
            description='A test report type',
            created_by=self.user
        )
        
        self.question = Question.objects.create(
            report_type=self.report_type,
            question_text='Test Question',
            question_type='text',
            order=1
        )

    def test_basic_urls_exist(self):
        """Test that basic URLs exist and can be reversed"""
        urls_to_test = [
            ('reports:report_type_list', {}),
            ('reports:report_type_detail', {'pk': self.report_type.pk}),
            ('reports:form_builder', {'report_type_id': self.report_type.pk}),
            ('reports:customer_assignments', {'report_type_id': self.report_type.pk}),
            ('reports:question_templates', {}),
        ]
        
        for url_name, kwargs in urls_to_test:
            with self.subTest(url=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    self.assertTrue(url.startswith('/'))  # Just check URL exists
                except Exception as e:
                    self.fail(f'URL {url_name} does not exist: {e}')

    def test_ajax_urls_exist(self):
        """Test that AJAX URLs exist"""
        ajax_urls_to_test = [
            ('reports:ajax_create_section', {'report_type_id': self.report_type.pk}),
            ('reports:ajax_create_question', {'report_type_id': self.report_type.pk}),
            ('reports:ajax_update_order', {'report_type_id': self.report_type.pk}),
        ]
        
        for url_name, kwargs in ajax_urls_to_test:
            with self.subTest(url=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    self.assertTrue(url.startswith('/'))
                except Exception as e:
                    self.fail(f'URL {url_name} does not exist: {e}')


class AdminTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.report_type = ReportType.objects.create(
            name='Admin Test Report',
            description='Test report for admin',
            created_by=self.user
        )
        
        self.customer_user = User.objects.create_user(
            username='customer2',
            email='customer2@example.com',
            password='customerpass123'
        )
        self.customer = Customer.objects.create(
            user=self.customer_user,
            businessName='Test Customer',
            phoneNumber='555-5678'
        )

    def test_admin_models_registered(self):
        """Test that our new models are registered in admin"""
        from django.contrib import admin
        
        # Check that our models are registered
        self.assertIn(ReportTypeCustomer, admin.site._registry)
        self.assertIn(QuestionTemplate, admin.site._registry)

    def test_report_type_customer_admin_display(self):
        """Test ReportTypeCustomer admin display methods"""
        from .admin import ReportTypeCustomerAdmin
        
        assignment = ReportTypeCustomer.objects.create(
            report_type=self.report_type,
            customer=self.customer,
            assigned_by=self.user
        )
        
        from django.contrib import admin
        admin_obj = ReportTypeCustomerAdmin(ReportTypeCustomer, admin.site)
        
        # Test custom display methods
        customer_name = admin_obj.customer_name(assignment)
        self.assertEqual(customer_name, 'Test Customer')


class IntegrationTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='integrationpass123'
        )
        self.client.login(username='integrationuser', password='integrationpass123')
        
        self.report_type = ReportType.objects.create(
            name='Integration Test Report',
            description='Test report for integration',
            created_by=self.user
        )

    def test_complete_workflow(self):
        """Test a complete workflow from report type to question creation"""
        # 1. Create a section
        section = ReportSection.objects.create(
            report_type=self.report_type,
            name='Test Section',
            order=1
        )
        
        # 2. Create a question
        question = Question.objects.create(
            report_type=self.report_type,
            section=section,
            question_text='Integration test question',
            question_type='text',
            order=1
        )
        
        # 3. Create a question template
        template = QuestionTemplate.objects.create(
            name='Integration Template',
            question_text='Template question',
            question_type='select',
            created_by=self.user
        )
        
        # 4. Create customer assignment
        customer_user = User.objects.create_user(
            username='customer3',
            email='customer3@example.com',
            password='customerpass123'
        )
        customer = Customer.objects.create(
            user=customer_user,
            businessName='Integration Customer',
            phoneNumber='555-9999'
        )
        
        assignment = ReportTypeCustomer.objects.create(
            report_type=self.report_type,
            customer=customer,
            assigned_by=self.user
        )
        
        # Verify everything was created
        self.assertEqual(ReportSection.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(QuestionTemplate.objects.count(), 1)
        self.assertEqual(ReportTypeCustomer.objects.count(), 1)
        
        # Test relationships
        self.assertEqual(question.section, section)
        self.assertEqual(assignment.report_type, self.report_type)
        self.assertEqual(assignment.customer, customer)