"""The report-type builder's JSON API, as the admin app calls it."""
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from chemsapp.models import Customer, Distributor

from .models import (
    Question, QuestionOption, Report, ReportSection, ReportType,
    ReportTypeCustomer, ReportTypeDistributor,
)


class BuilderTestCase(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            'builder', password='pw12345678', is_staff=True)
        self.token = Token.objects.get(user=self.staff).key
        self.report_type = ReportType.objects.create(
            name='Monthly Audit', category='standard', auto_number_prefix='MA',
            created_by=self.staff)
        self.produce = ReportSection.objects.create(
            report_type=self.report_type, name='Produce', order=0)
        self.bakery = ReportSection.objects.create(
            report_type=self.report_type, name='Bakery', order=1)
        self.clean = Question.objects.create(
            report_type=self.report_type, section=self.produce,
            question_text='Is the area clean?', question_type='yesno',
            is_required=True, order=0)
        self.why = Question.objects.create(
            report_type=self.report_type, section=self.produce,
            question_text='Why not?', question_type='text', order=1,
            parent_question=self.clean, show_when_parent_values=['no'])
        self.grade = Question.objects.create(
            report_type=self.report_type, section=self.bakery,
            question_text='Grade', question_type='radio', order=0)
        self.pass_option = QuestionOption.objects.create(
            question=self.grade, text='PASS', value='pass', badge_type='pass', order=0)
        self.fail_option = QuestionOption.objects.create(
            question=self.grade, text='FAIL', value='fail', badge_type='fail',
            is_flag=True, order=1)

    def post(self, name, args=(), data=None):
        return self.client.post(
            reverse(f'reports:{name}', args=args),
            data=json.dumps(data or {}), content_type='application/json',
            HTTP_ACCEPT='application/json', HTTP_AUTHORIZATION=f'Token {self.token}')

    def get(self, name, args=()):
        return self.client.get(
            reverse(f'reports:{name}', args=args),
            HTTP_ACCEPT='application/json', HTTP_AUTHORIZATION=f'Token {self.token}')


class TreeTests(BuilderTestCase):
    def test_tree_lists_sections_and_questions_in_app_order(self):
        tree = self.get('staff_api_report_type_tree', [self.report_type.pk]).json()['data']

        self.assertEqual([s['name'] for s in tree['sections']], ['Produce', 'Bakery'])
        self.assertEqual(
            [q['question_text'] for q in tree['questions']],
            ['Is the area clean?', 'Why not?', 'Grade'])
        why = tree['questions'][1]
        self.assertEqual(why['parent_question_id'], self.clean.pk)
        self.assertEqual(why['show_when_parent_values'], ['no'])
        self.assertEqual([o['value'] for o in tree['questions'][2]['options']], ['pass', 'fail'])

    def test_a_non_staff_token_is_refused(self):
        outsider = User.objects.create_user('outsider', password='pw12345678')
        response = self.client.get(
            reverse('reports:staff_api_report_type_tree', args=[self.report_type.pk]),
            HTTP_ACCEPT='application/json',
            HTTP_AUTHORIZATION=f'Token {Token.objects.get(user=outsider).key}')
        self.assertEqual(response.status_code, 403)


class ReportTypeTests(BuilderTestCase):
    def test_create_records_who_made_it(self):
        response = self.post('staff_api_report_type_create', data={
            'name': 'Site Visit', 'category': 'site_assessment', 'is_active': True})

        self.assertEqual(response.status_code, 200)
        created = ReportType.objects.get(name='Site Visit')
        self.assertEqual(created.created_by, self.staff)
        self.assertEqual(response.json()['data']['id'], created.pk)

    def test_create_reports_a_missing_name_on_the_field(self):
        response = self.post('staff_api_report_type_create', data={'category': 'standard'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.json()['errors'])

    def test_update_of_one_field_leaves_the_others_alone(self):
        self.post('staff_api_report_type_update', [self.report_type.pk],
                  {'description': 'Every month'})

        self.report_type.refresh_from_db()
        self.assertEqual(self.report_type.description, 'Every month')
        self.assertEqual(self.report_type.name, 'Monthly Audit')
        self.assertEqual(self.report_type.auto_number_prefix, 'MA')
        self.assertTrue(self.report_type.is_active)

    def test_delete_is_refused_while_reports_use_the_type(self):
        Report.objects.create(
            report_type=self.report_type, document_number='MA0001', prepared_by=self.staff)

        response = self.post('staff_api_report_type_delete', [self.report_type.pk])

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['report_count'], 1)
        self.assertTrue(ReportType.objects.filter(pk=self.report_type.pk).exists())

    def test_delete_with_force_removes_the_type_and_its_reports(self):
        Report.objects.create(
            report_type=self.report_type, document_number='MA0001', prepared_by=self.staff)

        response = self.post('staff_api_report_type_delete', [self.report_type.pk],
                             {'force': True})

        self.assertEqual(response.json()['data']['reports_deleted'], 1)
        self.assertFalse(ReportType.objects.filter(pk=self.report_type.pk).exists())

    def test_duplicate_copies_the_structure_with_its_conditions(self):
        response = self.post('staff_api_report_type_duplicate', [self.report_type.pk])

        tree = response.json()['data']
        self.assertEqual(tree['name'], 'Monthly Audit (Copy)')
        self.assertEqual(tree['prefix'], 'MAC')
        self.assertEqual(len(tree['sections']), 2)
        self.assertEqual(len(tree['questions']), 3)

        copy = ReportType.objects.get(pk=tree['id'])
        why = copy.questions.get(question_text='Why not?')
        # The copy's condition points at the copy's parent, not the original.
        self.assertEqual(why.parent_question.report_type, copy)
        self.assertEqual(why.get_show_when_values(), ['no'])
        self.assertEqual(copy.questions.get(question_text='Grade').options.count(), 2)


class SectionTests(BuilderTestCase):
    def test_a_new_section_goes_to_the_bottom(self):
        tree = self.post('staff_api_section_create', [self.report_type.pk],
                         {'name': 'Deli'}).json()['data']
        self.assertEqual([s['name'] for s in tree['sections']], ['Produce', 'Bakery', 'Deli'])

    def test_rename_keeps_the_order(self):
        self.post('staff_api_section_update', [self.bakery.pk], {'name': 'Bread'})
        self.bakery.refresh_from_db()
        self.assertEqual((self.bakery.name, self.bakery.order), ('Bread', 1))

    def test_duplicate_copies_questions_and_their_internal_conditions(self):
        tree = self.post('staff_api_section_duplicate', [self.produce.pk]).json()['data']

        copy = ReportSection.objects.get(name='Produce (Copy)')
        self.assertEqual(copy.questions.count(), 2)
        why = copy.questions.get(question_text='Why not?')
        self.assertEqual(why.parent_question.section, copy)
        self.assertEqual(len(tree['questions']), 5)

    def test_delete_removes_the_section_and_its_questions(self):
        self.post('staff_api_section_delete', [self.bakery.pk])
        self.assertFalse(Question.objects.filter(pk=self.grade.pk).exists())


class QuestionTests(BuilderTestCase):
    def test_create_in_a_section_goes_to_its_bottom(self):
        self.post('staff_api_question_create', [self.report_type.pk], {
            'question_text': 'Temperature', 'question_type': 'number',
            'section': self.produce.pk})

        added = Question.objects.get(question_text='Temperature')
        self.assertEqual((added.section, added.order), (self.produce, 2))

    def test_update_of_the_text_keeps_required_and_the_condition(self):
        self.post('staff_api_question_update', [self.why.pk], {'question_text': 'Why is it dirty?'})

        self.why.refresh_from_db()
        self.assertEqual(self.why.question_text, 'Why is it dirty?')
        self.assertEqual(self.why.parent_question, self.clean)
        self.assertEqual(self.why.get_show_when_values(), ['no'])

        self.post('staff_api_question_update', [self.clean.pk], {'help_text': 'Look closely'})
        self.clean.refresh_from_db()
        self.assertTrue(self.clean.is_required)

    def test_a_question_cannot_be_its_own_parent(self):
        response = self.post('staff_api_question_update', [self.clean.pk], {
            'parent_question': self.clean.pk, 'show_when_parent_values': ['yes']})

        self.assertEqual(response.status_code, 400)
        self.assertIn('parent_question', response.json()['errors'])

    def test_clearing_the_parent_clears_the_trigger_values(self):
        self.post('staff_api_question_update', [self.why.pk], {'parent_question': None})

        self.why.refresh_from_db()
        self.assertIsNone(self.why.parent_question)
        self.assertEqual(self.why.get_show_when_values(), [])

    def test_a_trigger_value_must_be_one_the_parent_offers(self):
        response = self.post('staff_api_question_update', [self.why.pk], {
            'parent_question': self.grade.pk, 'show_when_parent_values': ['maybe']})

        self.assertEqual(response.status_code, 400)
        self.assertIn('show_when_parent_values', response.json()['errors'])

    def test_deleting_a_parent_keeps_its_child_unconditional(self):
        self.post('staff_api_question_delete', [self.clean.pk])

        self.why.refresh_from_db()
        self.assertIsNone(self.why.parent_question)
        self.assertEqual(self.why.get_show_when_values(), [])

    def test_duplicate_places_the_copy_after_the_original(self):
        self.post('staff_api_question_duplicate', [self.grade.pk])

        copy = Question.objects.exclude(pk=self.grade.pk).get(question_text='Grade')
        self.assertEqual(copy.order, 1)
        self.assertEqual(copy.options.count(), 2)

    def test_the_old_page_no_longer_duplicates_on_get(self):
        self.client.login(username='builder', password='pw12345678')
        self.client.get(reverse('reports:question_duplicate', args=[self.grade.pk]))
        self.assertEqual(Question.objects.filter(question_text='Grade').count(), 1)


class OptionTests(BuilderTestCase):
    def test_create_goes_to_the_bottom(self):
        self.post('staff_api_option_create', [self.grade.pk], {'text': 'N/A', 'value': 'na'})
        self.assertEqual(QuestionOption.objects.get(value='na').order, 2)

    def test_update_of_the_text_keeps_the_flag(self):
        self.post('staff_api_option_update', [self.fail_option.pk], {'text': 'Failed'})
        self.fail_option.refresh_from_db()
        self.assertEqual(self.fail_option.text, 'Failed')
        self.assertTrue(self.fail_option.is_flag)

    def test_reorder_writes_the_new_order(self):
        self.post('staff_api_option_reorder', [self.grade.pk],
                  {'ids': [self.fail_option.pk, self.pass_option.pk]})
        self.assertEqual(
            list(self.grade.options.order_by('order').values_list('value', flat=True)),
            ['fail', 'pass'])

    def test_reorder_refuses_another_questions_option(self):
        stray = QuestionOption.objects.create(question=self.clean, text='x', value='x')
        response = self.post('staff_api_option_reorder', [self.grade.pk], {'ids': [stray.pk]})
        self.assertEqual(response.status_code, 400)


class ReorderTests(BuilderTestCase):
    def test_sections_and_questions_take_the_dragged_order(self):
        self.post('staff_api_report_type_reorder', [self.report_type.pk], {
            'sections': [self.bakery.pk, self.produce.pk],
            'questions': [
                {'section': self.bakery.pk, 'ids': [self.grade.pk]},
                {'section': self.produce.pk, 'ids': [self.why.pk, self.clean.pk]},
            ],
        })

        self.bakery.refresh_from_db()
        self.why.refresh_from_db()
        self.assertEqual(self.bakery.order, 0)
        self.assertEqual(self.why.order, 0)

    def test_a_question_dragged_into_another_section_moves_there(self):
        self.post('staff_api_report_type_reorder', [self.report_type.pk], {
            'sections': [self.produce.pk, self.bakery.pk],
            'questions': [{'section': self.bakery.pk, 'ids': [self.clean.pk, self.grade.pk]}],
        })

        self.clean.refresh_from_db()
        self.assertEqual((self.clean.section, self.clean.order), (self.bakery, 0))

    def test_a_question_can_leave_every_section(self):
        self.post('staff_api_report_type_reorder', [self.report_type.pk], {
            'sections': [self.produce.pk, self.bakery.pk],
            'questions': [{'section': None, 'ids': [self.grade.pk]}],
        })
        self.grade.refresh_from_db()
        self.assertIsNone(self.grade.section)

    def test_another_types_question_is_refused(self):
        other = ReportType.objects.create(name='Other', created_by=self.staff)
        stray = Question.objects.create(
            report_type=other, question_text='Stray', question_type='text')

        response = self.post('staff_api_report_type_reorder', [self.report_type.pk], {
            'sections': [], 'questions': [{'section': self.produce.pk, 'ids': [stray.pk]}]})

        self.assertEqual(response.status_code, 400)
        stray.refresh_from_db()
        self.assertEqual(stray.report_type, other)


class AssignmentTests(BuilderTestCase):
    def setUp(self):
        super().setUp()
        user = User.objects.create(username='cafe', email='cafe@example.com')
        self.customer = Customer.objects.create(
            user=user, phoneNumber='1', businessName='Uno Cafe', address='1 Road')
        self.distributor = Distributor.objects.create(businessname='Otago Supplies')

    def test_assign_and_withdraw_a_customer(self):
        self.post('staff_api_report_type_assignment_set', [self.report_type.pk],
                  {'kind': 'customer', 'id': self.customer.pk, 'active': True})
        row = ReportTypeCustomer.objects.get(customer=self.customer)
        self.assertTrue(row.is_active)
        self.assertEqual(row.assigned_by, self.staff)

        self.post('staff_api_report_type_assignment_set', [self.report_type.pk],
                  {'kind': 'customer', 'id': self.customer.pk, 'active': False})
        row.refresh_from_db()
        # Withdrawn, but the row and its history stay.
        self.assertFalse(row.is_active)

    def test_assign_a_distributor(self):
        self.post('staff_api_report_type_assignment_set', [self.report_type.pk],
                  {'kind': 'distributor', 'id': self.distributor.pk, 'active': True})
        self.assertTrue(ReportTypeDistributor.objects.get(distributor=self.distributor).is_active)

    def test_the_type_lists_who_has_it(self):
        ReportTypeCustomer.objects.create(
            report_type=self.report_type, customer=self.customer, is_active=True)

        data = self.get('staff_api_report_type_assignments', [self.report_type.pk]).json()['data']

        cafe = next(c for c in data['customers'] if c['id'] == self.customer.pk)
        self.assertTrue(cafe['active'])
        otago = next(d for d in data['distributors'] if d['id'] == self.distributor.pk)
        self.assertFalse(otago['active'])

    def test_the_matrix_toggle_matches_the_old_admin_page(self):
        self.post('staff_api_assignment_toggle', data={
            'customer_id': self.customer.pk, 'report_type_id': self.report_type.pk,
            'active': True})

        matrix = self.get('staff_api_assignment_matrix').json()['data']
        self.assertIn([self.customer.pk, self.report_type.pk], matrix['active'])
