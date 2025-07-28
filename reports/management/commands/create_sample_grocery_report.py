from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from reports.models import ReportType, ReportSection, Question, QuestionOption


class Command(BaseCommand):
    help = 'Create a comprehensive sample grocery store audit report based on the CSV structure'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample grocery store audit report...'))
        
        # Get or create an admin user for the report type
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(username='admin').first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found. Please create a superuser first.'))
            return
        
        # Create the report type
        report_type, created = ReportType.objects.get_or_create(
            name="Monthly Audit Report - Grocery",
            defaults={
                'description': 'Comprehensive food safety and compliance audit for grocery stores',
                'auto_number_prefix': 'MAR',
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        if not created:
            self.stdout.write(self.style.WARNING('Report type already exists. Updating...'))
        
        # Create sections
        sections_data = [
            ("First Page", "Report header and basic information", 0),
            ("PRODUCE DEPARTMENT", "Produce department inspections and tests", 1),
            ("Overall Department Check", "General cleanliness and facility checks", 2),
            ("Food Contact Surfaces", "Equipment and utensil cleanliness", 3),
            ("Equipment Condition", "Equipment maintenance and repair status", 4),
        ]
        
        sections = {}
        for name, description, order in sections_data:
            section, created = ReportSection.objects.get_or_create(
                report_type=report_type,
                name=name,
                defaults={
                    'description': description,
                    'order': order
                }
            )
            sections[name] = section
            
        # Create questions based on CSV structure
        questions_data = [
            # First Page
            {
                'section': 'First Page',
                'text': 'Account (Client)',
                'type': 'client_select',
                'order': 1,
                'required': True,
                'help': 'Select the client/customer for this audit'
            },
            {
                'section': 'First Page',
                'text': 'Store Compliance Manager',
                'type': 'text',
                'order': 2,
                'required': True,
                'help': 'Name of the store compliance manager'
            },
            {
                'section': 'First Page',
                'text': 'Report Type (Month)',
                'type': 'select',
                'order': 3,
                'required': True,
                'options': [
                    ('January', 'january', False),
                    ('February', 'february', False),
                    ('March', 'march', False),
                    ('April', 'april', False),
                    ('May', 'may', False),
                    ('June', 'june', False),
                    ('July', 'july', False),
                    ('August', 'august', False),
                    ('September', 'september', False),
                    ('October', 'october', False),
                    ('November', 'november', False),
                    ('December', 'december', False),
                ]
            },
            {
                'section': 'First Page',
                'text': 'Inspection Date',
                'type': 'date',
                'order': 4,
                'required': True,
                'help': 'Date when the inspection was conducted'
            },
            {
                'section': 'First Page',
                'text': 'Report Prepared By',
                'type': 'text',
                'order': 5,
                'required': True,
                'help': 'Name of the person preparing this report'
            },
            
            # Produce Department
            {
                'section': 'PRODUCE DEPARTMENT',
                'text': 'Concentration of Sanitiser in Spray Bottles in Produce Dept',
                'type': 'radio',
                'order': 10,
                'required': True,
                'options': [
                    ('PASS', 'pass', False),
                    ('N/A', 'na', False),
                    ('FAIL', 'fail', True, 'Incorrect Concentration of Sanitiser in Spray Bottles in Produce Dept'),
                ]
            },
            {
                'section': 'PRODUCE DEPARTMENT',
                'text': 'If FAIL - Select the concentration reading',
                'type': 'radio',
                'order': 11,
                'parent_question': 'Concentration of Sanitiser in Spray Bottles in Produce Dept',
                'show_when': 'fail',
                'options': [
                    ('0ppm', '0ppm', True),
                    ('50ppm', '50ppm', True),
                    ('100ppm', '100ppm', True),
                    ('150ppm', '150ppm', True),
                    ('450+ppm', '450+ppm', True),
                ]
            },
            {
                'section': 'PRODUCE DEPARTMENT',
                'text': 'Concentration of Sanitiser in Tong Tanks/Buckets in Produce Dept',
                'type': 'radio',
                'order': 12,
                'required': True,
                'options': [
                    ('PASS', 'pass', False),
                    ('N/A', 'na', False),
                    ('FAIL', 'fail', True, 'Incorrect Concentration of Sanitiser in Tong Tanks In Produce Dept'),
                ]
            },
            {
                'section': 'PRODUCE DEPARTMENT',
                'text': 'Are chemicals authorized, labeled/stored properly and have correct Chemical in them? Are the Correct Tools being Used? in Produce?',
                'type': 'radio',
                'order': 13,
                'required': True,
                'options': [
                    ('PASS', 'pass', False),
                    ('N/A', 'na', False),
                    ('FAIL', 'fail', True, 'Issue with incorrect Labeling, storage or use of Chemicals in Produce Dept'),
                ]
            },
            {
                'section': 'PRODUCE DEPARTMENT',
                'text': 'If chemicals FAIL - Select the issue',
                'type': 'radio',
                'order': 14,
                'parent_question': 'Are chemicals authorized, labeled/stored properly and have correct Chemical in them? Are the Correct Tools being Used? in Produce?',
                'show_when': 'fail',
                'options': [
                    ('Spray Bottle not labeled', 'spray_bottle_unlabeled', True),
                    ('Unapproved chemicals present', 'unapproved_chemicals', True),
                    ('Spray Bottle has incorrect Chemical in it', 'incorrect_chemical', True),
                    ('Unapproved Scrubbing pads being used', 'unapproved_scrubbing_pads', True),
                ]
            },
            
            # Overall Department Check
            {
                'section': 'Overall Department Check',
                'text': 'Are all non-food contact work and floor areas clean and physical facilities in good repair in Produce Dept?',
                'type': 'radio',
                'order': 20,
                'required': True,
                'options': [
                    ('N/A', 'na', False),
                    ('Good Retail Practice - General Cleanliness OK', 'good', False),
                    ('Critical', 'critical', True),
                    ('Potentially Critical', 'potentially_critical', True),
                    ('Needs Attention', 'needs_attention', True),
                ]
            },
            {
                'section': 'Overall Department Check',
                'text': 'If NOT Good - Select the specific issue',
                'type': 'checkbox',
                'order': 21,
                'parent_question': 'Are all non-food contact work and floor areas clean and physical facilities in good repair in Produce Dept?',
                'show_when': 'critical,potentially_critical,needs_attention',
                'options': [
                    ('Build-up observed on non-food contact surface', 'buildup_surface', True),
                    ('Dirty floors observed (Where Duel is Used)', 'dirty_floors_duel', True),
                    ('Dirty vents and/or ceilings observed', 'dirty_vents', True),
                    ('Condensation was observed', 'condensation', True),
                    ('Dirty walls observed', 'dirty_walls', True),
                    ('Dirty drains observed', 'dirty_drains', True),
                    ('Insects present', 'insects', True),
                    ('Insects: flies/fruit flies present', 'flies', True),
                    ('Build-up observed on shelving & storage surfaces', 'buildup_shelving', True),
                    ('Build up of Biofilm in Sinks', 'biofilm_sinks', True),
                    ('Buildup of Scale in Dishwasher', 'scale_dishwasher', True),
                ]
            },
            
            # Food Contact Surfaces
            {
                'section': 'Food Contact Surfaces',
                'text': 'Are food contact surfaces, equipment and utensils properly cleaned in Produce Dept?',
                'type': 'radio',
                'order': 30,
                'required': True,
                'options': [
                    ('N/A', 'na', False),
                    ('Good Retail Practice - General Cleanliness OK', 'good', False),
                    ('Critical', 'critical', True),
                    ('Potentially Critical', 'potentially_critical', True),
                    ('Needs Attention', 'needs_attention', True),
                ]
            },
            
            # Equipment Condition
            {
                'section': 'Equipment Condition',
                'text': 'Is all equipment in good repair in Produce Dept?',
                'type': 'radio',
                'order': 40,
                'required': True,
                'options': [
                    ('Yes', 'yes', False),
                    ('N/A', 'na', False),
                    ('No', 'no', True, 'Equipment needs repair or attention'),
                ]
            },
            {
                'section': 'Equipment Condition',
                'text': 'If equipment needs repair - Add notes',
                'type': 'textarea',
                'order': 41,
                'parent_question': 'Is all equipment in good repair in Produce Dept?',
                'show_when': 'no',
                'help': 'Describe what equipment needs repair and the issues observed'
            },
        ]
        
        # Create questions and options
        question_objects = {}
        for q_data in questions_data:
            section = sections.get(q_data['section'])
            
            question, created = Question.objects.get_or_create(
                report_type=report_type,
                question_text=q_data['text'],
                defaults={
                    'section': section,
                    'question_type': q_data['type'],
                    'order': q_data['order'],
                    'is_required': q_data.get('required', False),
                    'help_text': q_data.get('help', ''),
                }
            )
            
            question_objects[q_data['text']] = question
            
            # Add options if they exist
            if 'options' in q_data:
                for option_data in q_data['options']:
                    text, value = option_data[0], option_data[1]
                    is_flag = option_data[2] if len(option_data) > 2 else False
                    instructions = option_data[3] if len(option_data) > 3 else ''
                    
                    QuestionOption.objects.get_or_create(
                        question=question,
                        text=text,
                        defaults={
                            'value': value,
                            'is_flag': is_flag,
                            'additional_instructions': instructions,
                            'order': len(question.options.all())
                        }
                    )
        
        # Set up conditional logic for parent questions
        for q_data in questions_data:
            if 'parent_question' in q_data:
                question = question_objects[q_data['text']]
                parent = question_objects[q_data['parent_question']]
                question.parent_question = parent
                question.show_when_parent_value = q_data.get('show_when', '')
                question.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample grocery store audit report!\n'
                f'Report Type: {report_type.name}\n'
                f'Sections: {len(sections)}\n'
                f'Questions: {len(questions_data)}\n'
                f'Visit: /reports/{report_type.pk}/ to view the form builder'
            )
        )