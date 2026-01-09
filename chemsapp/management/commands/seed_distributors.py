"""
Management command to seed the database with test distributor data.
Usage: python manage.py seed_distributors
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chemsapp.models import Distributor, Customer, Product, ProductCategory, Profile


class Command(BaseCommand):
    help = 'Seeds the database with test distributor, user, and customer data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))

        # Create some products and categories first
        category1, _ = ProductCategory.objects.get_or_create(
            name='Cleaning Products',
            defaults={'description': 'Industrial cleaning chemicals'}
        )
        category2, _ = ProductCategory.objects.get_or_create(
            name='Safety Equipment',
            defaults={'description': 'Personal protective equipment'}
        )

        product1, _ = Product.objects.get_or_create(
            productCode='CLEAN-001',
            defaults={
                'name': 'Industrial Cleaner Pro',
                'brand': 'CleanTech',
                'description': 'Heavy-duty industrial cleaning solution',
                'directions': 'Dilute 1:10 with water. Apply and rinse.',
            }
        )
        product1.productCategory.add(category1)

        product2, _ = Product.objects.get_or_create(
            productCode='SAFE-001',
            defaults={
                'name': 'Safety Goggles',
                'brand': 'SafetyFirst',
                'description': 'Impact-resistant safety goggles',
                'directions': 'Wear when handling chemicals',
            }
        )
        product2.productCategory.add(category2)

        self.stdout.write(self.style.SUCCESS(f'Created/found {Product.objects.count()} products'))

        # Create distributors with users
        distributors_data = [
            {
                'businessname': 'ABC Chemical Distributors',
                'phonenumber': '555-0101',
                'cellphonenumber': '555-0102',
                'address': '123 Chemical Way, Auckland, New Zealand',
                'users': [
                    {'username': 'john_abc', 'email': 'john@abcchemical.co.nz', 'first_name': 'John', 'last_name': 'Smith'},
                    {'username': 'sarah_abc', 'email': 'sarah@abcchemical.co.nz', 'first_name': 'Sarah', 'last_name': 'Johnson'},
                ]
            },
            {
                'businessname': 'XYZ Supply Co',
                'phonenumber': '555-0201',
                'cellphonenumber': '555-0202',
                'address': '456 Supply Street, Wellington, New Zealand',
                'users': [
                    {'username': 'mike_xyz', 'email': 'mike@xyzsupply.co.nz', 'first_name': 'Mike', 'last_name': 'Williams'},
                ]
            },
            {
                'businessname': 'Pacific Distribution Ltd',
                'phonenumber': '555-0301',
                'cellphonenumber': '555-0302',
                'address': '789 Pacific Drive, Christchurch, New Zealand',
                'users': [
                    {'username': 'emma_pacific', 'email': 'emma@pacificdist.co.nz', 'first_name': 'Emma', 'last_name': 'Brown'},
                    {'username': 'david_pacific', 'email': 'david@pacificdist.co.nz', 'first_name': 'David', 'last_name': 'Wilson'},
                    {'username': 'lisa_pacific', 'email': 'lisa@pacificdist.co.nz', 'first_name': 'Lisa', 'last_name': 'Taylor'},
                ]
            },
        ]

        for dist_data in distributors_data:
            users_data = dist_data.pop('users')

            # Create distributor
            distributor, created = Distributor.objects.get_or_create(
                businessname=dist_data['businessname'],
                defaults=dist_data
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created distributor: {distributor.businessname}'))
            else:
                self.stdout.write(self.style.WARNING(f'Distributor already exists: {distributor.businessname}'))

            # Create users for this distributor
            for user_data in users_data:
                username = user_data['username']
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults=user_data
                )

                if user_created:
                    # Set a default password
                    user.set_password('testpass123')
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'  Created user: {username} (password: testpass123)'))

                    # Create profile for user
                    Profile.objects.get_or_create(
                        user=user,
                        defaults={
                            'phoneNumber': distributor.phonenumber,
                            'businessName': user.get_full_name() or username,
                            'address': distributor.address,
                            'profileType': 'distributor'
                        }
                    )
                else:
                    self.stdout.write(self.style.WARNING(f'  User already exists: {username}'))

                # Associate user with distributor
                if user not in distributor.users.all():
                    distributor.users.add(user)
                    self.stdout.write(self.style.SUCCESS(f'  Associated {username} with {distributor.businessname}'))

        # Create some customers
        customers_data = [
            {
                'businessName': 'Acme Manufacturing',
                'phoneNumber': '555-1001',
                'address': '100 Factory Road, Auckland',
                'user_data': {'username': 'acme_admin', 'email': 'admin@acme.com', 'first_name': 'Admin', 'last_name': 'Acme'}
            },
            {
                'businessName': 'BuildCo Industries',
                'phoneNumber': '555-1002',
                'address': '200 Builder Ave, Wellington',
                'user_data': {'username': 'buildco_admin', 'email': 'admin@buildco.com', 'first_name': 'Admin', 'last_name': 'BuildCo'}
            },
        ]

        for customer_data in customers_data:
            user_data = customer_data.pop('user_data')

            # Create user first
            user, user_created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )

            if user_created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created customer user: {user.username}'))

            # Create customer
            customer, created = Customer.objects.get_or_create(
                user=user,
                defaults=customer_data
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created customer: {customer.businessName}'))
                # Add some products to customer
                customer.products.add(product1, product2)
            else:
                self.stdout.write(self.style.WARNING(f'Customer already exists: {customer.businessName}'))

        # Associate customers with first distributor
        first_distributor = Distributor.objects.first()
        if first_distributor:
            for customer in Customer.objects.all():
                if customer not in first_distributor.customers.all():
                    first_distributor.customers.add(customer)
            self.stdout.write(self.style.SUCCESS(f'Associated customers with {first_distributor.businessname}'))

        # Print summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Database seeding completed!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'Distributors: {Distributor.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Customers: {Customer.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Products: {Product.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Users: {User.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('\nDefault login credentials:'))
        self.stdout.write(self.style.WARNING('  Username: john_abc'))
        self.stdout.write(self.style.WARNING('  Password: testpass123'))
        self.stdout.write(self.style.SUCCESS('='*50))
