"""Importer for the customers spreadsheet (e.g. "Customer-2026-09-16 update.xlsx").

Shared by the `import_customers` customer dashboard view. Sheet layout: two
sheets, row-matched by business name —

"Customers" sheet, header row 1, data from row 2: businessName, phoneNumber,
address (read by header name, so column order does not matter).

"Users" sheet, header row 1, data from row 2: one contact per customer —
First Name, Last Name, Email Address.

A customer already in the database (matched by the contact's email, which
is the Django username) is skipped, never updated. The spreadsheet's
"group" column is not read: on the local database no CustomerGroup exists
yet to match it against, so an imported customer starts with no group and
staff assign one afterwards on the dashboard's Groups tab.
"""
import random
import string

import openpyxl
from django.contrib.auth.models import User
from django.db import transaction

from chemsapp.models import Customer, CustomerContact

CUSTOMERS_SHEET = 'Customers'
USERS_SHEET = 'Users'
HEADER_ROW = 1
FIRST_DATA_ROW = 2


def _header_map(sheet):
    """{lowercase header text: column number} from the sheet's header row."""
    headers = {}
    for cell in sheet[HEADER_ROW]:
        if cell.value:
            headers[str(cell.value).strip().lower()] = cell.column
    return headers


def _cell(sheet, row, headers, name):
    column = headers.get(name)
    if column is None:
        return ''
    value = sheet.cell(row=row, column=column).value
    return str(value).strip() if value is not None else ''


def _random_password():
    return ''.join(random.choice(string.ascii_letters) for _ in range(10))


def import_customers_workbook(file_or_path):
    """Run the import against an xlsx file (path or file-like object).

    Must be called inside a transaction (the caller owns dry-run
    semantics). Returns a stats dict: created, skipped_existing, errors
    (lists of strings).
    """
    workbook = openpyxl.load_workbook(file_or_path, data_only=True)
    customers_sheet = workbook[CUSTOMERS_SHEET]
    users_sheet = workbook[USERS_SHEET]

    customers_headers = _header_map(customers_sheet)
    users_headers = _header_map(users_sheet)

    contacts_by_business = {}
    for row in range(FIRST_DATA_ROW, users_sheet.max_row + 1):
        business_name = _cell(users_sheet, row, users_headers, 'customer')
        if not business_name:
            continue
        contacts_by_business[business_name] = {
            'first_name': _cell(users_sheet, row, users_headers, 'first name'),
            'last_name': _cell(users_sheet, row, users_headers, 'last name'),
            'email': _cell(users_sheet, row, users_headers, 'email address'),
        }

    existing_emails = {
        email.lower()
        for email in User.objects.exclude(email='').values_list('email', flat=True)
    }

    stats = {'created': [], 'skipped_existing': [], 'errors': []}

    for row in range(FIRST_DATA_ROW, customers_sheet.max_row + 1):
        business_name = _cell(customers_sheet, row, customers_headers, 'businessname')
        if not business_name:
            continue

        contact = contacts_by_business.get(business_name)
        if contact is None:
            stats['errors'].append(f'{business_name} — no contact row in the Users sheet')
            continue

        email = contact['email']
        if not email:
            stats['errors'].append(f'{business_name} — no email address for the contact')
            continue

        if email.lower() in existing_emails:
            stats['skipped_existing'].append(f'{business_name} — {email} already has an account')
            continue

        phone_number = _cell(customers_sheet, row, customers_headers, 'phonenumber')
        address = _cell(customers_sheet, row, customers_headers, 'address')

        try:
            # A savepoint, not the outer transaction: one bad row (e.g. a
            # stale id sequence) must not poison every row after it.
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=contact['first_name'],
                    last_name=contact['last_name'],
                )
                user.set_password(_random_password())
                user.save()

                customer = Customer.objects.create(
                    user=user,
                    businessName=business_name,
                    phoneNumber=phone_number,
                    address=address,
                    profileType='customer',
                    hasSetPassword=False,
                )

                contact_name = f"{contact['first_name']} {contact['last_name']}".strip()
                CustomerContact.objects.create(
                    customer=customer, name=contact_name or email, email=email)
        except Exception as e:
            stats['errors'].append(f'{business_name} — {e}')
            continue

        existing_emails.add(email.lower())
        stats['created'].append(f'{business_name} — {email}')

    return stats
