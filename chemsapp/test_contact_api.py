"""The website-contacts JSON API, as the admin app calls it."""
import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token

from chemsapp.models import Contact, Product


class ContactApiTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('contacts-staff', password='pw12345678', is_staff=True)
        self.auth = {'HTTP_AUTHORIZATION': f'Token {Token.objects.get(user=self.staff).key}'}
        self.product = Product.objects.create(
            name='Citrus Degreaser', description='d', directions='d', productCode='CD1', brand='b')
        self.enquiry = Contact.objects.create(
            nameFrom='Jane Smith', emailFrom='jane@acme.test', companyName='Acme',
            content='Please send a price list.')
        self.linked_sds = Contact.objects.create(
            nameFrom='Bob Jones', emailFrom='bob@kiwi.test', companyName='Kiwi Clean',
            isSDSDownload=True, product=self.product, distributorName='Bunzl',
            content='Downloaded SDS for product:Citrus Degreaser')
        self.old_sds = Contact.objects.create(
            nameFrom='Ann Lee', emailFrom='ann@old.test', isSDSDownload=True,
            content='Downloaded SDS for product:Glass Cleaner', replied=True)
        # Give each row a different date. The newest is the enquiry.
        now = timezone.now()
        for days, contact in enumerate([self.enquiry, self.linked_sds, self.old_sds]):
            Contact.objects.filter(pk=contact.pk).update(created_at=now - timedelta(days=days))
        self.list_url = reverse('staff_api_contact_list')

    def detail_url(self, contact):
        return reverse('staff_api_contact_detail', args=[contact.pk])

    def get_list(self, **params):
        return self.client.get(self.list_url, params, **self.auth).json()['data']

    def test_str_is_the_name(self):
        self.assertEqual(str(self.enquiry), 'Jane Smith')

    def test_non_staff_is_refused(self):
        plain = User.objects.create_user('contacts-plain', password='pw12345678')
        token = Token.objects.get(user=plain).key
        response = self.client.get(self.list_url, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 403)

    def test_list_is_newest_first_with_both_kinds(self):
        data = self.get_list()
        self.assertEqual([row['name'] for row in data['contacts']],
                         ['Jane Smith', 'Bob Jones', 'Ann Lee'])
        self.assertEqual(data['total'], 3)
        enquiry, linked, old = data['contacts']
        self.assertEqual(enquiry['kind'], 'enquiry')
        self.assertEqual(enquiry['message'], 'Please send a price list.')
        self.assertIsNone(enquiry['product_name'])
        self.assertEqual(linked['kind'], 'sds')
        self.assertEqual(linked['product_id'], self.product.pk)
        self.assertEqual(linked['product_name'], 'Citrus Degreaser')
        self.assertEqual(linked['company'], 'Kiwi Clean')
        self.assertEqual(linked['distributor'], 'Bunzl')
        self.assertEqual(enquiry['distributor'], '')
        self.assertEqual(linked['message'], '')

    def test_old_sds_row_takes_the_product_name_from_content(self):
        old = self.get_list()['contacts'][2]
        self.assertIsNone(old['product_id'])
        self.assertEqual(old['product_name'], 'Glass Cleaner')
        self.assertEqual(old['company'], '')

    def test_kind_filter(self):
        self.assertEqual([r['name'] for r in self.get_list(kind='enquiry')['contacts']],
                         ['Jane Smith'])
        self.assertEqual([r['name'] for r in self.get_list(kind='sds')['contacts']],
                         ['Bob Jones', 'Ann Lee'])

    def test_replied_filter(self):
        self.assertEqual([r['name'] for r in self.get_list(replied='1')['contacts']],
                         ['Ann Lee'])
        self.assertEqual(len(self.get_list(replied='0')['contacts']), 2)

    def test_search_finds_company_and_product_text(self):
        self.assertEqual([r['name'] for r in self.get_list(q='acme')['contacts']],
                         ['Jane Smith'])
        self.assertEqual([r['name'] for r in self.get_list(q='glass')['contacts']],
                         ['Ann Lee'])
        self.assertEqual([r['name'] for r in self.get_list(q='bunzl')['contacts']],
                         ['Bob Jones'])

    def test_patch_sets_replied(self):
        response = self.client.patch(
            self.detail_url(self.enquiry), json.dumps({'replied': True}),
            content_type='application/json', **self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data']['replied'])
        self.enquiry.refresh_from_db()
        self.assertTrue(self.enquiry.replied)

    def test_patch_refuses_a_value_that_is_not_a_boolean(self):
        response = self.client.patch(
            self.detail_url(self.enquiry), json.dumps({'replied': 'yes'}),
            content_type='application/json', **self.auth)
        self.assertEqual(response.status_code, 400)

    def test_patch_does_not_change_other_fields(self):
        self.client.patch(
            self.detail_url(self.enquiry), json.dumps({'replied': True, 'nameFrom': 'X'}),
            content_type='application/json', **self.auth)
        self.enquiry.refresh_from_db()
        self.assertEqual(self.enquiry.nameFrom, 'Jane Smith')


class SdsEnquireProductLinkTests(TestCase):
    @mock.patch('chemsapp.views.mail_admin_async')
    @mock.patch('chemsapp.views.push_sds_to_onepagecrm')
    def test_sds_enquire_saves_the_product_link(self, _crm, _mail):
        product = Product.objects.create(
            name='Floor Polish', description='d', directions='d', productCode='FP1', brand='b')
        payload = {'nameFrom': 'Sam', 'emailFrom': 'sam@x.test',
                   'companyName': 'X Ltd', 'productId': product.pk}
        self.client.get('/sds_enquire/',
                        {'data': json.dumps(payload)})
        contact = Contact.objects.get(emailFrom='sam@x.test')
        self.assertTrue(contact.isSDSDownload)
        self.assertEqual(contact.product, product)
        self.assertEqual(contact.content, 'Downloaded SDS for product:Floor Polish')

    @mock.patch('chemsapp.views.mail_admin_async')
    @mock.patch('chemsapp.views.push_sds_to_onepagecrm')
    def test_sds_enquire_saves_the_distributor(self, crm, mail):
        product = Product.objects.create(
            name='Floor Polish', description='d', directions='d', productCode='FP2', brand='b')
        payload = {'nameFrom': 'Kim', 'emailFrom': 'kim@x.test', 'companyName': '',
                   'distributorName': 'Bunzl Auckland', 'productId': product.pk}
        self.client.get('/sds_enquire/', {'data': json.dumps(payload)})
        contact = Contact.objects.get(emailFrom='kim@x.test')
        self.assertEqual(contact.distributorName, 'Bunzl Auckland')
        self.assertEqual(crm.call_args[0][0]['distributorName'], 'Bunzl Auckland')
        self.assertIn('Distributor: Bunzl Auckland', mail.call_args[0][1])

    @mock.patch('chemsapp.views.mail_admin_async')
    @mock.patch('chemsapp.views.push_sds_to_onepagecrm')
    def test_sds_enquire_works_without_a_distributor(self, _crm, mail):
        product = Product.objects.create(
            name='Floor Polish', description='d', directions='d', productCode='FP3', brand='b')
        payload = {'nameFrom': 'Lee', 'emailFrom': 'lee@x.test', 'productId': product.pk}
        self.client.get('/sds_enquire/', {'data': json.dumps(payload)})
        contact = Contact.objects.get(emailFrom='lee@x.test')
        self.assertIsNone(contact.distributorName)
        self.assertIn('Distributor: \n', mail.call_args[0][1])
