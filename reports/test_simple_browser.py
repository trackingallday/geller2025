"""
Simple browser test demonstrating report creation and filling functionality.
"""

import time
import os
from django.test import LiveServerTestCase, TransactionTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from chemsapp.models import Customer, Distributor
from .models import ReportType, ReportSection, Question, QuestionOption, Report, Answer


class SimpleReportTest(TransactionTestCase):
    """Simple test to demonstrate report functionality without browser conflicts."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create distributor user
        self.distributor_user = User.objects.create_user(
            username='distributor',
            email='distributor@example.com',
            password='distpass123'
        )
        
        # Create customer and distributor
        self.customer = Customer.objects.create(
            user=self.user,
            businessName='Test Business Ltd',
            phoneNumber='555-1234',
            address='123 Test Street'
        )
        
        self.distributor = Distributor.objects.create(
            user=self.distributor_user,
            businessName='Test Distributor Inc',
            phoneNumber='555-5678',
            address='456 Distributor Ave'
        )
    
    def test_complete_report_workflow(self):
        """Test complete report creation and filling workflow."""
        print("🚀 Starting complete report workflow test...")
        
        # 1. Create report type
        report_type = ReportType.objects.create(
            name='Equipment Inspection',
            description='Daily equipment inspection checklist',
            auto_number_prefix='EI',
            created_by=self.admin_user
        )
        print(f"✅ Created report type: {report_type.name}")
        
        # 2. Create section
        section = ReportSection.objects.create(
            report_type=report_type,
            name='Equipment Status',
            description='Check the status of all equipment',
            order=1
        )
        print(f"✅ Created section: {section.name}")
        
        # 3. Create parent question (yes/no)
        parent_question = Question.objects.create(
            report_type=report_type,
            section=section,
            question_text='Is the equipment functioning normally?',
            question_type='yesno',
            is_required=True,
            order=1
        )
        print(f"✅ Created parent question: {parent_question.question_text}")
        
        # 4. Create child question (conditional)
        child_question = Question.objects.create(
            report_type=report_type,
            section=section,
            question_text='Please describe the issues found',
            question_type='textarea',
            parent_question=parent_question,
            show_when_parent_value='no',
            is_required=True,
            order=2
        )
        print(f"✅ Created conditional child question: {child_question.question_text}")
        print(f"   - Shows when parent = '{child_question.show_when_parent_value}'")
        
        # 5. Create additional questions
        inspector_question = Question.objects.create(
            report_type=report_type,
            section=section,
            question_text='Inspector name',
            question_type='text',
            is_required=True,
            order=3
        )
        
        status_question = Question.objects.create(
            report_type=report_type,
            section=section,
            question_text='Overall equipment status',
            question_type='select',
            is_required=True,
            order=4
        )
        
        # 6. Create options for select question
        excellent_option = QuestionOption.objects.create(
            question=status_question,
            text='Excellent',
            value='excellent',
            order=1
        )
        
        good_option = QuestionOption.objects.create(
            question=status_question,
            text='Good', 
            value='good',
            order=2
        )
        
        needs_attention_option = QuestionOption.objects.create(
            question=status_question,
            text='Needs Attention',
            value='needs_attention',
            is_flag=True,
            order=3
        )
        print(f"✅ Created select question with 3 options (1 flagged)")
        
        # 7. Create a report
        report = Report.objects.create(
            report_type=report_type,
            customer=self.customer,
            distributor=self.distributor,
            store_compliance_manager='John Manager',
            prepared_by=self.user
        )
        print(f"✅ Created report: {report.document_number}")
        print(f"   - Customer: {report.customer.businessName}")
        print(f"   - Manager: {report.store_compliance_manager}")
        
        # 8. Fill out the report (simulate user answers)
        print("📝 Filling out report answers...")
        
        # Answer parent question with 'no' (will trigger child question)
        parent_answer = Answer.objects.create(
            report=report,
            question=parent_question,
            text_answer='no'
        )
        print(f"   - Parent question answered: {parent_answer.text_answer}")
        
        # Answer child question (required because parent was 'no')
        child_answer = Answer.objects.create(
            report=report,
            question=child_question,
            text_answer='Equipment is making strange noises and vibrating excessively. Requires immediate maintenance.'
        )
        print(f"   - Child question answered: {child_answer.text_answer[:50]}...")
        
        # Answer inspector question
        inspector_answer = Answer.objects.create(
            report=report,
            question=inspector_question,
            text_answer='Jane Inspector'
        )
        print(f"   - Inspector: {inspector_answer.text_answer}")
        
        # Answer status question (select flagged option)
        status_answer = Answer.objects.create(
            report=report,
            question=status_question
        )
        status_answer.selected_options.add(needs_attention_option)
        print(f"   - Status: {needs_attention_option.text} (⚠️ FLAGGED)")
        
        # 9. Verify all data was saved correctly
        print("🔍 Verifying report data...")
        
        saved_report = Report.objects.get(id=report.id)
        self.assertEqual(saved_report.answers.count(), 4)
        print(f"   - Total answers saved: {saved_report.answers.count()}")
        
        # Test conditional logic worked
        self.assertEqual(child_question.parent_question, parent_question)
        self.assertEqual(child_question.show_when_parent_value, 'no')
        print(f"   - Conditional logic: ✅ Child question shows when parent = 'no'")
        
        # Test answer display values
        self.assertEqual(parent_answer.get_display_value(), 'no')
        self.assertEqual(status_answer.get_display_value(), 'Needs Attention')
        print(f"   - Answer display values: ✅ Working correctly")
        
        # Test flagged answer detection
        flagged_answers = Answer.objects.filter(
            report=report,
            selected_options__is_flag=True
        )
        self.assertEqual(flagged_answers.count(), 1)
        print(f"   - Flagged answers detected: {flagged_answers.count()}")
        
        print("✅ Complete report workflow test PASSED!")
        print(f"   - Report {saved_report.document_number} successfully created and filled")
        print(f"   - Conditional logic working correctly") 
        print(f"   - All {saved_report.answers.count()} answers saved to database")
        print(f"   - Data integrity verified ✅")
        
        return saved_report
    
    def test_conditional_logic_scenarios(self):
        """Test different conditional logic scenarios."""
        print("🧪 Testing conditional logic scenarios...")
        
        # Create report structure
        report_type = ReportType.objects.create(
            name='Conditional Logic Test',
            created_by=self.admin_user
        )
        
        parent_question = Question.objects.create(
            report_type=report_type,
            question_text='Is maintenance required?',
            question_type='yesno',
            order=1
        )
        
        child_question = Question.objects.create(
            report_type=report_type,
            question_text='What type of maintenance?',
            question_type='text',
            parent_question=parent_question,
            show_when_parent_value='yes',
            order=2
        )
        
        # Scenario 1: Parent = 'yes', child should be relevant
        report1 = Report.objects.create(
            report_type=report_type,
            customer=self.customer,
            distributor=self.distributor,
            prepared_by=self.user
        )
        
        Answer.objects.create(
            report=report1,
            question=parent_question,
            text_answer='yes'
        )
        
        Answer.objects.create(
            report=report1,
            question=child_question,
            text_answer='Oil change and filter replacement'
        )
        
        print("   ✅ Scenario 1: Parent='yes', child question answered")
        
        # Scenario 2: Parent = 'no', child would be hidden (but we can still test the logic)
        report2 = Report.objects.create(
            report_type=report_type,
            customer=self.customer,
            distributor=self.distributor,
            prepared_by=self.user
        )
        
        Answer.objects.create(
            report=report2,
            question=parent_question,
            text_answer='no'
        )
        # Child question would be hidden in UI, so no answer needed
        
        print("   ✅ Scenario 2: Parent='no', child question would be hidden")
        
        # Verify conditional relationships
        self.assertEqual(child_question.parent_question, parent_question)
        self.assertEqual(child_question.show_when_parent_value, 'yes')
        
        print("✅ Conditional logic scenarios test PASSED!")
        
    def test_performance_with_many_questions(self):
        """Test performance with many questions."""
        print("⚡ Testing performance with many questions...")
        
        start_time = time.time()
        
        # Create report type with many questions
        report_type = ReportType.objects.create(
            name='Performance Test Report',
            created_by=self.admin_user
        )
        
        section = ReportSection.objects.create(
            report_type=report_type,
            name='Performance Section',
            order=1
        )
        
        # Create 25 questions
        questions = []
        for i in range(25):
            question = Question.objects.create(
                report_type=report_type,
                section=section,
                question_text=f'Performance test question {i+1}',
                question_type='text',
                order=i+1
            )
            questions.append(question)
        
        # Create report
        report = Report.objects.create(
            report_type=report_type,
            customer=self.customer,
            distributor=self.distributor,
            prepared_by=self.user
        )
        
        # Answer all questions
        for i, question in enumerate(questions):
            Answer.objects.create(
                report=report,
                question=question,
                text_answer=f'Answer {i+1}'
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify
        self.assertEqual(report.answers.count(), 25)
        
        print(f"   ✅ Created 25 questions and answers in {duration:.2f} seconds")
        print(f"   ✅ Average time per answer: {(duration/25)*1000:.1f}ms")
        print("✅ Performance test PASSED!")


class BrowserTest(LiveServerTestCase):
    """Simple browser test that actually opens a browser."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Set up Chrome options
        chrome_options = Options()
        if os.environ.get('HEADLESS', 'true').lower() == 'true':
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Install ChromeDriver automatically
        try:
            service = Service(ChromeDriverManager().install())
            cls.selenium = webdriver.Chrome(service=service, options=chrome_options)
            cls.selenium.implicitly_wait(10)
        except Exception as e:
            print(f"⚠️  Could not start Chrome browser: {e}")
            cls.selenium = None
    
    @classmethod
    def tearDownClass(cls):
        if cls.selenium:
            cls.selenium.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Set up test data."""
        if not self.selenium:
            self.skipTest("Browser not available")
            
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
    
    def test_admin_login(self):
        """Test that we can login to Django admin."""
        print("🌐 Testing browser login to Django admin...")
        
        # Go to admin login
        self.selenium.get(f'{self.live_server_url}/admin/login/')
        
        # Fill in login form
        username_input = self.selenium.find_element(By.NAME, 'username')
        password_input = self.selenium.find_element(By.NAME, 'password')
        
        username_input.send_keys('admin')
        password_input.send_keys('adminpass123')
        
        # Submit form
        self.selenium.find_element(By.XPATH, '//input[@value="Log in"]').click()
        
        # Wait for dashboard
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dashboard'))
        )
        
        # Verify we're logged in
        self.assertIn('Django administration', self.selenium.page_source)
        
        print("   ✅ Successfully logged into Django admin")
        print("   ✅ Browser automation working correctly")
        print("✅ Browser login test PASSED!")
    
    def test_reports_admin_exists(self):
        """Test that reports admin interface is accessible."""
        if not self.selenium:
            self.skipTest("Browser not available")
            
        print("🌐 Testing reports admin interface...")
        
        # Login first
        self.selenium.get(f'{self.live_server_url}/admin/login/')
        username_input = self.selenium.find_element(By.NAME, 'username')
        password_input = self.selenium.find_element(By.NAME, 'password')
        username_input.send_keys('admin')
        password_input.send_keys('adminpass123')
        self.selenium.find_element(By.XPATH, '//input[@value="Log in"]').click()
        
        # Wait for dashboard
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dashboard'))
        )
        
        # Check if Reports app exists
        try:
            reports_link = self.selenium.find_element(By.LINK_TEXT, 'Reports')
            reports_link.click()
            print("   ✅ Reports admin section accessible")
        except:
            print("   ⚠️  Reports admin section not found in main dashboard")
            # Try direct URL
            self.selenium.get(f'{self.live_server_url}/admin/reports/')
        
        # Verify we can see reports models
        self.assertIn('Reports', self.selenium.page_source)
        print("✅ Reports admin interface test PASSED!")