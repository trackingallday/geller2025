"""
Test script to generate a full sample report with random images for PDF testing.
Run with: python manage.py test reports.test_pdf_generation.PDFGenerationTest.test_generate_full_report
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from chemsapp.models import Customer, Distributor
from reports.models import (
    ReportType, ReportSection, Question, QuestionOption,
    Report, Answer
)
from PIL import Image, ImageDraw, ImageFont
import io
import random
import uuid


class PDFGenerationTest(TestCase):
    """Test PDF generation with comprehensive sample data"""

    def generate_random_image(self, width=800, height=600, text="Test Image"):
        """Generate a random colored image with text"""
        # Random background color
        bg_color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )

        # Create image
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Draw some random shapes
        for _ in range(5):
            shape_type = random.choice(['rectangle', 'ellipse', 'line'])
            color = (
                random.randint(0, 200),
                random.randint(0, 200),
                random.randint(0, 200)
            )

            x1, y1 = random.randint(0, width-100), random.randint(0, height-100)
            x2, y2 = x1 + random.randint(50, 150), y1 + random.randint(50, 150)

            if shape_type == 'rectangle':
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            elif shape_type == 'ellipse':
                draw.ellipse([x1, y1, x2, y2], outline=color, width=3)
            else:
                draw.line([x1, y1, x2, y2], fill=color, width=5)

        # Add text
        text_color = (0, 0, 0)
        text_size = 40
        text_position = (width // 4, height // 2)

        try:
            # Try to use a default font
            draw.text(text_position, text, fill=text_color)
        except Exception:
            # Fallback if font not available
            draw.text(text_position, text, fill=text_color)

        # Save to BytesIO
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return ContentFile(buffer.read(), name=f'{text.replace(" ", "_")}.png')

    def generate_signature_image(self, name="Signature"):
        """Generate a simple signature-like image"""
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)

        # Draw signature-like scribble
        points = []
        for i in range(20):
            x = 20 + i * 13 + random.randint(-5, 5)
            y = 50 + random.randint(-20, 20)
            points.append((x, y))

        # Draw connected lines
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=(0, 0, 139), width=2)

        # Add name below
        draw.text((100, 70), name, fill=(0, 0, 0))

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return ContentFile(buffer.read(), name=f'signature_{name}.png')

    def test_generate_full_report(self):
        """Generate a comprehensive test report with all features"""
        print("\n" + "="*60)
        print("GENERATING FULL TEST REPORT FOR PDF")
        print("="*60)

        unique_id = str(uuid.uuid4())[:8]

        # Create test user
        user = User.objects.create_user(
            username=f'test_user_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            first_name='James',
            last_name='Rawnsley'
        )
        print(f"✓ Created user: {user.username}")

        # Create customer
        customer_user = User.objects.create_user(
            username=f'customer_{unique_id}',
            email=f'customer_{unique_id}@example.com',
            password='pass123'
        )
        customer = Customer.objects.create(
            user=customer_user,
            businessName="PAK'nSAVE Albany Store #507101",
            address="Albany, Auckland"
        )
        print(f"✓ Created customer: {customer.businessName}")

        # Create Report Type
        report_type = ReportType.objects.create(
            name="March Monthly Audit Report",
            description="Monthly audit for food retail stores",
            auto_number_prefix="Audit No",
            is_active=True,
            created_by=user
        )
        print(f"✓ Created report type: {report_type.name}")

        # Create Sections
        sections_data = [
            ("PRODUCE DEPARTMENT", "Produce department inspection"),
            ("BUTCHERY DEPARTMENT", "Butchery department inspection"),
            ("DELI DEPARTMENT", "Deli department inspection"),
            ("SEAFOOD DEPARTMENT", "Seafood department inspection"),
            ("BAKERY DEPARTMENT", "Bakery department inspection"),
        ]

        sections = []
        for idx, (name, desc) in enumerate(sections_data):
            section = ReportSection.objects.create(
                report_type=report_type,
                name=name,
                description=desc,
                order=idx
            )
            sections.append(section)
        print(f"✓ Created {len(sections)} sections")

        # Create Questions with various types
        questions = []

        # PRODUCE DEPARTMENT Questions
        q1 = Question.objects.create(
            report_type=report_type,
            section=sections[0],
            question_text="Concentration of Sanitiser in Spray Bottles in Produce Dept:",
            question_type='select',
            is_required=True,
            order=1
        )
        QuestionOption.objects.create(question=q1, text="Pass", value="pass", order=1)
        QuestionOption.objects.create(question=q1, text="Fail", value="fail", is_flag=True, order=2)
        questions.append(q1)

        q2 = Question.objects.create(
            report_type=report_type,
            section=sections[0],
            question_text="PPM Strength:",
            question_type='number',
            help_text="Enter PPM value (200-400 range recommended)",
            is_required=True,
            order=2
        )
        questions.append(q2)

        q3 = Question.objects.create(
            report_type=report_type,
            section=sections[0],
            question_text="Concentration of Sanitiser in Tong Tanks/Buckets in Produce Dept:",
            question_type='select',
            is_required=True,
            order=3
        )
        QuestionOption.objects.create(question=q3, text="Pass", value="pass", order=1)
        QuestionOption.objects.create(question=q3, text="Fail", value="fail", is_flag=True, order=2)
        questions.append(q3)

        q4 = Question.objects.create(
            report_type=report_type,
            section=sections[0],
            question_text="Fail : Incorrect Concentration of Sanitiser in Tong Tanks In Produce Dept:",
            question_type='text',
            order=4
        )
        questions.append(q4)

        q5 = Question.objects.create(
            report_type=report_type,
            section=sections[0],
            question_text="Are chemicals authorized, labeled/stored properly and have correct Chemical in them? Are the Correct Tools being Used? in Produce?",
            question_type='select',
            is_required=True,
            order=5
        )
        QuestionOption.objects.create(question=q5, text="Pass", value="pass", order=1)
        QuestionOption.objects.create(question=q5, text="Fail", value="fail", is_flag=True, order=2)
        questions.append(q5)

        q6 = Question.objects.create(
            report_type=report_type,
            section=sections[0],
            question_text="Swab in Produce taken on:",
            question_type='text',
            help_text="Specify location of swab test",
            order=6
        )
        questions.append(q6)

        q7 = Question.objects.create(
            report_type=report_type,
            section=sections[0],
            question_text="Result of swab in Produce Dept:",
            question_type='select',
            is_required=True,
            order=7
        )
        QuestionOption.objects.create(question=q7, text="Pass", value="pass", order=1)
        QuestionOption.objects.create(question=q7, text="Fail", value="fail", is_flag=True, order=2)
        questions.append(q7)

        q8 = Question.objects.create(
            report_type=report_type,
            section=sections[0],
            question_text="Issue, Comments and Suggested Corrective Action for Failed Swab in Produce Dept:",
            question_type='textarea',
            help_text="Describe the issue and corrective actions taken",
            order=8
        )
        questions.append(q8)

        q9 = Question.objects.create(
            report_type=report_type,
            section=sections[0],
            question_text="Are all non-food contact work and floor areas clean and physical facilities in good repair in Produce Dept?",
            question_type='select',
            is_required=True,
            order=9
        )
        QuestionOption.objects.create(question=q9, text="Good Retail Practice - General Cleanliness OK", value="ok", order=1)
        QuestionOption.objects.create(question=q9, text="Needs Attention", value="needs_attention", is_flag=True, order=2)
        questions.append(q9)

        # BUTCHERY Questions
        q10 = Question.objects.create(
            report_type=report_type,
            section=sections[1],
            question_text="Concentration of Sanitiser in Spray Bottles in Butchery Dept:",
            question_type='select',
            is_required=True,
            order=1
        )
        QuestionOption.objects.create(question=q10, text="Pass", value="pass", order=1)
        QuestionOption.objects.create(question=q10, text="Fail", value="fail", is_flag=True, order=2)
        questions.append(q10)

        q11 = Question.objects.create(
            report_type=report_type,
            section=sections[1],
            question_text="Is all equipment in good repair in Butchery Dept?",
            question_type='text',
            help_text="Specify any issues or reminders",
            is_required=True,
            order=2
        )
        questions.append(q11)

        # DELI Questions
        q12 = Question.objects.create(
            report_type=report_type,
            section=sections[2],
            question_text="Are chemicals authorized, labeled/stored properly and have correct Chemical in them? Are the Correct Tools being Used? in Deli?",
            question_type='select',
            is_required=True,
            order=1
        )
        QuestionOption.objects.create(question=q12, text="Pass", value="pass", order=1)
        QuestionOption.objects.create(question=q12, text="Fail", value="fail", is_flag=True, order=2)
        questions.append(q12)

        q13 = Question.objects.create(
            report_type=report_type,
            section=sections[2],
            question_text="Issue with incorrect Labeling, storage or use of Chemicals in Deli Dept:",
            question_type='text',
            order=2
        )
        questions.append(q13)

        q14 = Question.objects.create(
            report_type=report_type,
            section=sections[2],
            question_text="Issue with non-food contact surfaces and areas in Deli Dept:",
            question_type='text',
            order=3
        )
        questions.append(q14)

        q15 = Question.objects.create(
            report_type=report_type,
            section=sections[2],
            question_text="Is the Sanitiser /Dishwasher in Good Working condition the Deli?",
            question_type='text',
            order=4
        )
        questions.append(q15)

        print(f"✓ Created {len(questions)} questions")

        # Create Report
        report = Report.objects.create(
            report_type=report_type,
            customer=customer,
            store_compliance_manager="Example Manager",
            inspection_date=timezone.now().date(),
            prepared_by=user,
            status='submitted',
            submitted_at=timezone.now()
        )
        print(f"✓ Created report: {report.document_number}")

        # Create Answers with various types and images
        print("\n" + "-"*60)
        print("Creating answers with images and signatures...")
        print("-"*60)

        # Produce Department Answers
        answer1 = Answer.objects.create(report=report, question=q1)
        answer1.selected_options.add(QuestionOption.objects.get(question=q1, value="pass"))
        print("✓ Q1: Sanitiser spray bottles - Pass")

        answer2 = Answer.objects.create(report=report, question=q2, number_answer=300)
        print("✓ Q2: PPM Strength - 300 ppm")

        answer3 = Answer.objects.create(report=report, question=q3)
        answer3.selected_options.add(QuestionOption.objects.get(question=q3, value="fail"))
        print("✓ Q3: Tong tanks - Fail (FLAGGED)")

        answer4 = Answer.objects.create(report=report, question=q4, text_answer="0 ppm")
        print("✓ Q4: Issue description - 0 ppm (FLAGGED)")

        answer5 = Answer.objects.create(report=report, question=q5)
        answer5.selected_options.add(QuestionOption.objects.get(question=q5, value="pass"))
        print("✓ Q5: Chemical storage - Pass")

        # Add swab test with image
        answer6 = Answer.objects.create(report=report, question=q6, text_answer="Mesh Glove")
        answer6.file_answer = self.generate_random_image(800, 600, "Mesh Glove")
        answer6.save()
        print("✓ Q6: Swab location - Mesh Glove (with image)")

        answer7 = Answer.objects.create(report=report, question=q7)
        answer7.selected_options.add(QuestionOption.objects.get(question=q7, value="fail"))
        print("✓ Q7: Swab result - Fail (FLAGGED)")

        # Add corrective action with signature
        answer8 = Answer.objects.create(
            report=report,
            question=q8,
            text_answer="Failed Swab on Cutting Board/Table",
            notes="Soiled Surfaces can harbour bacteria and can contaminate foods. Use Ultimo Block Cleaner/Whitener, apply liberally at the end of the day and let sit over night with boards sandwiched together. In the morning scrub, rinse and sanitise. Repeat 4 times in a week until buildup has cleared. ENSURE that staff wear the appropriate PPE when using this product (Gloves, Goggles, Apron, Respirator Mask etc.)\n\nConducted coaching and training session with the staff member/s in the department to ensure adherence to the correct cleaning procedures. Subsequently, implemented corrective actions to address any identified areas of improvement."
        )
        answer8.signature_answer = self.generate_signature_image("Pat")
        answer8.attachment = self.generate_random_image(640, 480, "Cutting Board")
        answer8.save()
        print("✓ Q8: Corrective action with signature and photo")

        answer9 = Answer.objects.create(report=report, question=q9)
        answer9.selected_options.add(QuestionOption.objects.get(question=q9, value="ok"))
        print("✓ Q9: General cleanliness - OK")

        # Butchery Answers
        answer10 = Answer.objects.create(report=report, question=q10)
        answer10.selected_options.add(QuestionOption.objects.get(question=q10, value="pass"))
        answer10.file_answer = self.generate_random_image(800, 600, "Scales")
        answer10.save()
        print("✓ Q10: Butchery sanitiser - Pass (with image)")

        answer11 = Answer.objects.create(
            report=report,
            question=q11,
            text_answer="Reminder - Descale Foaming Machine",
            notes="Lime Off cleaner effectively removes hard water deposits and lime scale from the Tubing, internal parts and Hoses, nozzles and jets. Even the slightest amount can decrease performance and increase energy cost and create issues with the Foaming performance."
        )
        print("✓ Q11: Equipment repair - Reminder (FLAGGED)")

        # Deli Answers
        answer12 = Answer.objects.create(report=report, question=q12)
        answer12.selected_options.add(QuestionOption.objects.get(question=q12, value="fail"))
        print("✓ Q12: Deli chemicals - Fail (FLAGGED)")

        answer13 = Answer.objects.create(
            report=report,
            question=q13,
            text_answer="Unapproved Scrubbing pads being used.",
            notes="Team is using unapproved Scrubbing pads which is not allowed due to regulatory requirements and fragment matter issues. Please use Ultimo Scrubbing pads as attached product information sheet.\n\nConducted coaching and training session with the staff member/s in the department to ensure adherence to the correct procedures."
        )
        answer13.signature_answer = self.generate_signature_image("Harry")
        answer13.save()
        print("✓ Q13: Labeling issue - Unapproved pads (FLAGGED, with signature)")

        answer14 = Answer.objects.create(
            report=report,
            question=q14,
            text_answer="Dirty floors observed. (Where Duel is Used)",
            notes="Soiled floors observed. Soils can contaminate foods and attract pests. There is a build-up of soiling upon the department flooring. To clean the affected floor areas, I would suggest to - Sweep the floor free of any lose litter, soil, food scraps etc. apply floor cleaner scrub onto the affected areas & allow to soak for 10-30mins, scrub again then squeegee residue into the nearest floor drain, rinse with warm water if necessary. Ensure floors are kept clean at all times."
        )
        answer14.signature_answer = self.generate_signature_image("Kerry")
        answer14.save()
        print("✓ Q14: Dirty floors (FLAGGED, with signature)")

        answer15 = Answer.objects.create(
            report=report,
            question=q15,
            text_answer="Needs Descaling",
            notes="Lime Off cleaner effectively removes hard water deposits and lime scale from Sanitiser/dishmachines and surrounding stainless steel. Lime scale builds-up on Sanitiser rinse arms, nozzles and jets."
        )
        answer15.signature_answer = self.generate_signature_image("Bill")
        answer15.file_answer = self.generate_random_image(800, 600, "Dishwasher")
        answer15.save()
        print("✓ Q15: Dishwasher needs descaling (FLAGGED, with signature and photo)")

        # Generate PDF
        print("\n" + "="*60)
        print("GENERATING PDF...")
        print("="*60)

        success = report.generate_pdf()

        if success:
            print(f"✅ PDF GENERATED SUCCESSFULLY!")
            print(f"   Document Number: {report.document_number}")
            print(f"   PDF File: {report.pdf_file.name}")
            print(f"   PDF Path: {report.pdf_file.path if report.pdf_file else 'N/A'}")

            # Display statistics
            stats = report.get_flagged_statistics()
            print(f"\n   Statistics:")
            print(f"   - Flagged Items: {stats['flagged_count']}")
            print(f"   - Actions: {stats['action_count']}")
            print(f"   - Total Questions: {len(questions)}")
            print(f"   - Total Answers: {report.answers.count()}")
            print(f"   - Images: {report.answers.exclude(file_answer='').count()}")
            print(f"   - Signatures: {report.answers.exclude(signature_answer='').count()}")

            print("\n" + "="*60)
            print("TEST COMPLETED SUCCESSFULLY!")
            print("="*60)
        else:
            print(f"❌ PDF GENERATION FAILED")
            self.fail("PDF generation failed")

        # Verify PDF exists
        self.assertIsNotNone(report.pdf_file)
        self.assertTrue(report.pdf_file.name.endswith('.pdf'))
        print(f"\n✅ All assertions passed!")
