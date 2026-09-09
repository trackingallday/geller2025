"""Tests for the customer dashboard at /customer-dashboard/."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from chemsapp.models import Customer, CustomerContact, CustomerGroup


def make_customer(username, business, group=None):
    user = User.objects.create(username=username, email=f'{username}@example.com')
    return Customer.objects.create(
        user=user, phoneNumber='123', businessName=business, address='1 Road',
        group=group)


class CustomerGroupModelTests(TestCase):
    def test_str_is_the_name(self):
        group = CustomerGroup.objects.create(name='North Island')
        self.assertEqual(str(group), 'North Island')

    def test_customer_starts_with_no_group(self):
        customer = make_customer('acme', 'Acme Ltd')
        self.assertIsNone(customer.group)

    def test_deleting_a_group_frees_its_customers(self):
        group = CustomerGroup.objects.create(name='South Island')
        customer = make_customer('south', 'Southern Ltd', group=group)
        group.delete()
        customer.refresh_from_db()
        self.assertIsNone(customer.group)
        self.assertTrue(Customer.objects.filter(pk=customer.pk).exists())


class CustomerDashboardAccessTests(TestCase):
    def setUp(self):
        self.url = reverse('customer_dashboard')

    def test_signed_out_user_is_sent_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_non_staff_user_is_refused(self):
        User.objects.create_user('plain', password='pw12345678')
        self.client.login(username='plain', password='pw12345678')
        response = self.client.get(self.url, {'view': 'groups'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_staff_user_can_open_both_views(self):
        User.objects.create_user('staffer', password='pw12345678', is_staff=True)
        self.client.login(username='staffer', password='pw12345678')
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(
            self.client.get(self.url, {'view': 'groups'}).status_code, 200)


class CustomerDashboardTests(TestCase):
    def setUp(self):
        User.objects.create_user('staffer', password='pw12345678', is_staff=True)
        self.client.login(username='staffer', password='pw12345678')
        self.url = reverse('customer_dashboard')
        self.north = CustomerGroup.objects.create(name='North Island')
        self.south = CustomerGroup.objects.create(name='South Island')
        self.acme = make_customer('acme', 'Acme Cleaning')
        self.bay = make_customer('bay', 'Bay Services')
        self.southern = make_customer('southern', 'Southern Facilities')

    # --- per-customer group control ---

    def test_set_customer_group_moves_and_then_re_moves(self):
        set_url = reverse('set_customer_group', args=[self.acme.pk])
        self.client.post(set_url, {'group': self.north.pk})
        self.acme.refresh_from_db()
        self.assertEqual(self.acme.group, self.north)

        self.client.post(set_url, {'group': self.south.pk})
        self.acme.refresh_from_db()
        self.assertEqual(self.acme.group, self.south)
        # One group at a time: the FK just holds the last value.
        self.assertEqual(self.south.customers.count(), 1)
        self.assertEqual(self.north.customers.count(), 0)

    def test_set_customer_group_blank_clears_it(self):
        self.acme.group = self.north
        self.acme.save()
        self.client.post(
            reverse('set_customer_group', args=[self.acme.pk]), {'group': ''})
        self.acme.refresh_from_db()
        self.assertIsNone(self.acme.group)

    def test_customer_list_search_matches_name_and_email(self):
        list_url = reverse('dashboard_customer_list')
        by_name = self.client.get(list_url, {'q': 'Bay'})
        self.assertContains(by_name, 'Bay Services')
        self.assertNotContains(by_name, 'Acme Cleaning')

        by_email = self.client.get(list_url, {'q': 'southern@example.com'})
        self.assertContains(by_email, 'Southern Facilities')

    # --- groups view ---

    def test_create_group_redirects_to_the_new_group(self):
        response = self.client.post(
            reverse('create_customer_group'), {'name': 'Key Accounts'})
        group = CustomerGroup.objects.get(name='Key Accounts')
        self.assertRedirects(
            response, f'{self.url}?view=groups&group={group.pk}',
            fetch_redirect_response=False)

    def test_create_group_rejects_a_duplicate_name(self):
        self.client.post(reverse('create_customer_group'), {'name': 'North Island'})
        self.assertEqual(CustomerGroup.objects.filter(name='North Island').count(), 1)

    def test_add_group_customers_adds_many_at_once(self):
        response = self.client.post(
            reverse('add_group_customers', args=[self.north.pk]),
            {'customer': [self.acme.pk, self.bay.pk, self.southern.pk]})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.north.customers.count(), 3)

    def test_add_group_customers_moves_a_customer_from_another_group(self):
        self.acme.group = self.south
        self.acme.save()
        self.client.post(
            reverse('add_group_customers', args=[self.north.pk]),
            {'customer': [self.acme.pk]})
        self.acme.refresh_from_db()
        self.assertEqual(self.acme.group, self.north)
        self.assertEqual(self.south.customers.count(), 0)

    def test_remove_group_customer_takes_out_one_only(self):
        for c in (self.acme, self.bay):
            c.group = self.north
            c.save()
        self.client.post(
            reverse('remove_group_customer', args=[self.north.pk, self.acme.pk]))
        self.acme.refresh_from_db()
        self.bay.refresh_from_db()
        self.assertIsNone(self.acme.group)
        self.assertEqual(self.bay.group, self.north)

    def test_group_customer_search_excludes_current_members(self):
        self.acme.group = self.north
        self.acme.save()
        response = self.client.get(
            reverse('dashboard_group_customer_search'),
            {'q': '', 'exclude_group': self.north.pk})
        names = [row['name'] for row in response.json()['results']]
        self.assertNotIn('Acme Cleaning', names)
        self.assertIn('Bay Services', names)

    def test_delete_group_keeps_the_customers(self):
        self.acme.group = self.north
        self.acme.save()
        self.client.post(reverse('delete_group', args=[self.north.pk]))
        self.assertFalse(CustomerGroup.objects.filter(pk=self.north.pk).exists())
        self.acme.refresh_from_db()
        self.assertIsNone(self.acme.group)
        self.assertTrue(Customer.objects.filter(pk=self.acme.pk).exists())

    def test_group_list_shows_the_member_count(self):
        self.acme.group = self.north
        self.acme.save()
        self.bay.group = self.north
        self.bay.save()
        response = self.client.get(
            reverse('dashboard_group_list'), {'q': 'North'})
        self.assertContains(response, 'North Island')
        self.assertContains(response, '2 customers')

    # --- customer details + contacts ---

    def test_save_customer_details(self):
        self.client.post(
            reverse('save_customer_details', args=[self.acme.pk]),
            {'businessName': 'Acme Clean Co', 'phoneNumber': '999',
             'cellPhoneNumber': '', 'address': '2 Road', 'geocodingDetail': ''})
        self.acme.refresh_from_db()
        self.assertEqual(self.acme.businessName, 'Acme Clean Co')

    def test_save_customer_contacts(self):
        data = {
            'contacts-TOTAL_FORMS': '1',
            'contacts-INITIAL_FORMS': '0',
            'contacts-MIN_NUM_FORMS': '0',
            'contacts-MAX_NUM_FORMS': '1000',
            'contacts-0-name': 'Jane Doe',
            'contacts-0-role': 'Manager',
            'contacts-0-email': 'jane@acme.example.com',
            'contacts-0-phone': '555',
        }
        self.client.post(
            reverse('save_customer_contacts', args=[self.acme.pk]), data)
        self.assertEqual(
            CustomerContact.objects.filter(customer=self.acme, name='Jane Doe').count(), 1)
