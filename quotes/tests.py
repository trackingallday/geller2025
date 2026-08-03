import tempfile
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from chemsapp.models import ApplicationType, DilutionVariant, Product, ProductVariant, Size
from .models import Quote, QuoteLine, generate_quote_number
from .services import build_cost_in_use_snapshot, format_cost_in_use


def make_product(**kwargs):
    defaults = dict(
        name='Conquest Dishwash Detergent',
        subheading='Automatic Machine Dishwashing Liquid',
        description='<p>Geller Conquest is a <strong>concentrated</strong> automatic dishwasher liquid.</p>',
        directions='Use as directed.',
        productCode='CONQUEST',
        brand='Geller',
    )
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def make_variant(product, volume_litres=None, **kwargs):
    """Variant factory; volume_litres creates/reuses a Size carrying the volume."""
    defaults = dict(code='CONQUEST20', pack_size=1, barcode='9400000000001')
    defaults.update(kwargs)
    if volume_litres is not None and 'size' not in defaults:
        defaults['size'], _ = Size.objects.get_or_create(
            name=f'{volume_litres} Litre',
            defaults={'desc': f'{volume_litres} Litre', 'amount': str(volume_litres), 'volume_litres': volume_litres},
        )
    return ProductVariant.objects.create(product=product, **defaults)


def make_application_type(**kwargs):
    defaults = dict(
        name='Floor Mop/Bucket - General Cleaning',
        category='Floor Mop/Bucket',
        value_kind=ApplicationType.RATIO,
        unit_volume_litres=Decimal('1'),
        unit_label='per litre',
    )
    defaults.update(kwargs)
    return ApplicationType.objects.create(**defaults)


class DilutionFillsTestCase(TestCase):
    serialized_rollback = True

    def setUp(self):
        self.product = make_product()
        self.variant = make_variant(self.product, volume_litres=Decimal('20'))

    def test_ratio_fills(self):
        mop = make_application_type()
        dilution = DilutionVariant.objects.create(
            variant=self.variant, application_type=mop, value=Decimal('100'))
        # 20L × 100 ÷ 1L = 2000 litres of solution per pack
        self.assertEqual(dilution.fills(), Decimal('2000.00'))

    def test_ratio_zero_means_undiluted(self):
        spray = make_application_type(
            name='Spray Bottle - General Cleaning', category='Spray Bottle',
            unit_volume_litres=Decimal('0.75'), unit_label='per 750ml spray bottle')
        rtu = make_variant(
            self.product, volume_litres=Decimal('0.5'), code='CONQUEST500', barcode='9400000000009')
        dilution = DilutionVariant.objects.create(
            variant=rtu, application_type=spray, value=Decimal('0'))
        # Undiluted: 0.5L pack fills a 750ml bottle 0.67 times
        self.assertEqual(dilution.fills(), Decimal('0.67'))

    def test_ml_per_litre_fills(self):
        sanitising = make_application_type(
            name='Sanitising 200-400ppm', category='Sanitising',
            value_kind=ApplicationType.ML_PER_LITRE, unit_label='per litre @ 200-400ppm')
        dilution = DilutionVariant.objects.create(
            variant=self.variant, application_type=sanitising, value=Decimal('120'))
        # 20,000ml ÷ 120ml dose = 166.67 litres of solution
        self.assertEqual(dilution.fills(), Decimal('166.67'))

    def test_ml_per_cycle_fills(self):
        autodose = make_application_type(
            name='AutoDose - Per Cycle', category='AutoDose',
            value_kind=ApplicationType.ML_PER_CYCLE, unit_volume_litres=None, unit_label='per cycle')
        dilution = DilutionVariant.objects.create(
            variant=self.variant, application_type=autodose, value=Decimal('50'))
        # 20,000ml ÷ 50ml per cycle = 400 cycles
        self.assertEqual(dilution.fills(), Decimal('400.00'))

    def test_no_value_gives_none(self):
        autodose = make_application_type(
            name='AutoDose - Per Cycle', value_kind=ApplicationType.ML_PER_CYCLE,
            unit_volume_litres=None, unit_label='per cycle')
        dilution = DilutionVariant.objects.create(
            variant=self.variant, application_type=autodose, value=None,
            note='Check manufacturer recommendation')
        self.assertIsNone(dilution.fills())

    def test_zero_dose_gives_none(self):
        sanitising = make_application_type(
            name='Sanitising 200-400ppm', value_kind=ApplicationType.ML_PER_LITRE,
            unit_label='per litre @ 200-400ppm')
        dilution = DilutionVariant.objects.create(
            variant=self.variant, application_type=sanitising, value=Decimal('0'))
        self.assertIsNone(dilution.fills())

    def test_missing_volume_gives_none(self):
        mop = make_application_type()
        bare = make_variant(self.product, code='CONQUESTX', barcode='9400000000002')
        dilution = DilutionVariant.objects.create(
            variant=bare, application_type=mop, value=Decimal('100'))
        self.assertIsNone(dilution.fills())


class CostFormattingTestCase(TestCase):
    serialized_rollback = True

    def test_under_a_dollar(self):
        self.assertEqual(format_cost_in_use(Decimal('0.4495')), '.45c')
        self.assertEqual(format_cost_in_use(Decimal('0.02')), '.02c')

    def test_dollar_and_over(self):
        self.assertEqual(format_cost_in_use(Decimal('1.199')), '$1.20')
        self.assertEqual(format_cost_in_use(Decimal('1.00')), '$1.00')

    def test_rounds_up_to_a_dollar(self):
        self.assertEqual(format_cost_in_use(Decimal('0.999')), '$1.00')

    def test_snapshot_shape(self):
        mop = make_application_type()
        product = make_product()
        variant = make_variant(product, volume_litres=Decimal('20'))
        dilution = DilutionVariant.objects.create(
            variant=variant, application_type=mop, value=Decimal('100'))
        snapshot = build_cost_in_use_snapshot(Decimal('100.00'), [dilution])
        self.assertEqual(snapshot, [{
            'label': 'Floor Mop/Bucket - General Cleaning',
            'unit_label': 'per litre',
            'fills': '2000.00',
            'cost': '0.05',
            'display': 'Floor Mop/Bucket - General Cleaning .05c per litre',
        }])

    def test_snapshot_note_only_entry(self):
        autodose = make_application_type(
            name='AutoDose - Per Cycle', value_kind=ApplicationType.ML_PER_CYCLE,
            unit_volume_litres=None, unit_label='per cycle')
        product = make_product()
        variant = make_variant(product, volume_litres=Decimal('20'))
        dilution = DilutionVariant.objects.create(
            variant=variant, application_type=autodose, value=None, note='Check manufacturer recommendation')
        snapshot = build_cost_in_use_snapshot(Decimal('100.00'), [dilution])
        self.assertEqual(snapshot[0]['display'], 'AutoDose - Per Cycle: Check manufacturer recommendation')
        self.assertIsNone(snapshot[0]['cost'])


class QuoteNumberTestCase(TestCase):
    serialized_rollback = True

    def test_sequential_numbers(self):
        q1 = Quote.objects.create(company_name='A')
        q2 = Quote.objects.create(company_name='B')
        self.assertEqual(q1.quote_number, 'Q0001')
        self.assertEqual(q2.quote_number, 'Q0002')

    def test_survives_legacy_non_numeric_value(self):
        Quote.objects.create(company_name='A')
        Quote.objects.filter(company_name='A').update(quote_number='QLEGACY')
        self.assertEqual(generate_quote_number(), 'Q0001')


@mock.patch('quotes.services.QuotePDFGenerator')
class SubmitQuoteAPITestCase(TestCase):
    serialized_rollback = True

    def setUp(self):
        self.user = User.objects.create_user(username='rep', email='rep@example.com', password='pass12345')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.mop = make_application_type()
        self.spray = make_application_type(
            name='Spray Bottle - General Cleaning', category='Spray Bottle',
            unit_volume_litres=Decimal('0.75'), unit_label='per 750ml spray bottle')
        self.product = make_product()
        self.variant = make_variant(self.product, volume_litres=Decimal('20'))
        self.mop_dilution = DilutionVariant.objects.create(
            variant=self.variant, application_type=self.mop, value=Decimal('100'))
        self.spray_dilution = DilutionVariant.objects.create(
            variant=self.variant, application_type=self.spray, value=Decimal('25'))

    def _payload(self, **overrides):
        payload = {
            'company_name': 'XYZ CAFE',
            'address': '29 BRIDGE ST\nCAMBRIDGE',
            'contact_name': 'Sam Brown',
            'lines': [{
                'product_variant_id': self.variant.pk,
                'price': '100.00',
                'dilution_ids': [self.mop_dilution.pk],
            }],
        }
        payload.update(overrides)
        return payload

    def test_submit_creates_quote_with_selected_dilutions(self, mock_pdf):
        response = self.client.post('/quotes/submit/', self._payload(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['quote_number'], 'Q0001')

        line = QuoteLine.objects.get()
        self.assertEqual(line.product_name, 'Conquest Dishwash Detergent')
        self.assertEqual(line.product_code, 'CONQUEST20')
        self.assertNotIn('<', line.description)
        # Only the selected mop option is snapshotted, not the spray one
        self.assertEqual(len(line.cost_in_use), 1)
        self.assertEqual(line.cost_in_use[0]['display'], 'Floor Mop/Bucket - General Cleaning .05c per litre')
        self.assertEqual(list(line.dilutions.all()), [self.mop_dilution])
        mock_pdf.assert_called_once()

    def test_submit_without_dilutions_gives_empty_cost_in_use(self, mock_pdf):
        payload = self._payload(lines=[{'product_variant_id': self.variant.pk, 'price': '100.00'}])
        response = self.client.post('/quotes/submit/', payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(QuoteLine.objects.get().cost_in_use, [])

    def test_dilution_of_other_variant_rejected(self, mock_pdf):
        other_product = make_product(name='Other', productCode='OTHER')
        other_variant = make_variant(other_product, code='OTHER05', barcode='9400000000003',
                                     volume_litres=Decimal('5'))
        foreign = DilutionVariant.objects.create(
            variant=other_variant, application_type=self.mop, value=Decimal('50'))
        payload = self._payload(lines=[{
            'product_variant_id': self.variant.pk, 'price': '100.00', 'dilution_ids': [foreign.pk],
        }])
        response = self.client.post('/quotes/submit/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Quote.objects.exists())

    def test_unknown_dilution_rejected(self, mock_pdf):
        payload = self._payload(lines=[{
            'product_variant_id': self.variant.pk, 'price': '100.00', 'dilution_ids': [99999],
        }])
        response = self.client.post('/quotes/submit/', payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_snapshot_frozen_against_dilution_changes(self, mock_pdf):
        self.client.post('/quotes/submit/', self._payload(), format='json')
        self.mop_dilution.value = Decimal('50')
        self.mop_dilution.save()
        line = QuoteLine.objects.get()
        self.assertEqual(line.cost_in_use[0]['cost'], '0.05')  # unchanged

    def test_empty_lines_rejected(self, mock_pdf):
        response = self.client.post('/quotes/submit/', self._payload(lines=[]), format='json')
        self.assertEqual(response.status_code, 400)

    def test_unknown_variant_rejected(self, mock_pdf):
        response = self.client.post(
            '/quotes/submit/',
            self._payload(lines=[{'product_variant_id': 99999, 'price': '10.00'}]),
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Quote.objects.exists())

    def test_catalogue_lists_dilution_options(self, mock_pdf):
        response = self.client.get('/quotes/catalogue/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        item = response.data[0]
        self.assertEqual(item['code'], 'CONQUEST20')
        options = {o['application_type']: o for o in item['dilution_options']}
        self.assertEqual(options['Floor Mop/Bucket - General Cleaning']['fills'], '2000.00')
        self.assertEqual(options['Spray Bottle - General Cleaning']['value'], '25.00')

    def test_catalogue_hides_inactive_application_types(self, mock_pdf):
        self.spray.is_active = False
        self.spray.save()
        response = self.client.get('/quotes/catalogue/')
        names = [o['application_type'] for o in response.data[0]['dilution_options']]
        self.assertEqual(names, ['Floor Mop/Bucket - General Cleaning'])

    def test_list_and_mine_filter(self, mock_pdf):
        self.client.post('/quotes/submit/', self._payload(), format='json')
        other = User.objects.create_user(username='other', email='other@example.com', password='pass12345')
        Quote.objects.create(company_name='Someone else', created_by=other)

        response = self.client.get('/quotes/')
        self.assertEqual(len(response.data), 2)
        response = self.client.get('/quotes/?mine=1')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], 'XYZ CAFE')


@mock.patch('quotes.services.QuotePDFGenerator')
class DashboardTestCase(TestCase):
    serialized_rollback = True

    def setUp(self):
        self.user = User.objects.create_user(username='staff', email='staff@example.com', password='pass12345')
        self.client.force_login(self.user)

        self.mop = make_application_type()
        self.product = make_product()
        self.variant = make_variant(self.product, volume_litres=Decimal('20'))
        self.dilution = DilutionVariant.objects.create(
            variant=self.variant, application_type=self.mop, value=Decimal('100'))

    def test_requires_login(self, mock_pdf):
        self.client.logout()
        response = self.client.get('/quotes/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_dashboard_lists_quotes(self, mock_pdf):
        quote = Quote.objects.create(company_name='XYZ CAFE', created_by=self.user)
        response = self.client.get('/quotes/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'XYZ CAFE')

        response = self.client.get(f'/quotes/dashboard/?quote={quote.pk}')
        self.assertContains(response, f'Proposal {quote.quote_number}')

    def test_create_page_renders_builder(self, mock_pdf):
        response = self.client.get('/quotes/dashboard/create/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'catalogue-data')
        self.assertContains(response, 'Conquest Dishwash Detergent')
        self.assertContains(response, 'dilution_options')

    def test_create_quote_with_selected_dilution(self, mock_pdf):
        response = self.client.post('/quotes/dashboard/create/', {
            'company_name': 'XYZ CAFE',
            'address': '29 BRIDGE ST\nCAMBRIDGE',
            'contact_name': 'Sam Brown',
            'customer_id': '',
            'variant_id': [str(self.variant.pk)],
            'price': ['100.00'],
            'dilution_id': [str(self.dilution.pk)],
        })
        self.assertEqual(response.status_code, 302)
        quote = Quote.objects.get()
        self.assertEqual(quote.company_name, 'XYZ CAFE')
        self.assertEqual(quote.created_by, self.user)
        line = quote.lines.get()
        self.assertEqual(len(line.cost_in_use), 1)
        self.assertEqual(line.cost_in_use[0]['display'], 'Floor Mop/Bucket - General Cleaning .05c per litre')
        self.assertEqual(list(line.dilutions.all()), [self.dilution])
        mock_pdf.assert_called_once()

    def test_create_quote_without_dilution_has_no_cost_in_use(self, mock_pdf):
        response = self.client.post('/quotes/dashboard/create/', {
            'company_name': 'XYZ CAFE',
            'variant_id': [str(self.variant.pk)],
            'price': ['100.00'],
            'dilution_id': [''],
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Quote.objects.get().lines.get().cost_in_use, [])

    def test_create_rejects_foreign_dilution(self, mock_pdf):
        other_product = make_product(name='Other', productCode='OTHER')
        other_variant = make_variant(other_product, code='OTHER05', barcode='9400000000004',
                                     volume_litres=Decimal('5'))
        foreign = DilutionVariant.objects.create(
            variant=other_variant, application_type=self.mop, value=Decimal('50'))
        response = self.client.post('/quotes/dashboard/create/', {
            'company_name': 'XYZ CAFE',
            'variant_id': [str(self.variant.pk)],
            'price': ['100.00'],
            'dilution_id': [str(foreign.pk)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'does not belong')
        self.assertFalse(Quote.objects.exists())

    def test_create_rejects_missing_price(self, mock_pdf):
        response = self.client.post('/quotes/dashboard/create/', {
            'company_name': 'XYZ CAFE',
            'variant_id': [str(self.variant.pk)],
            'price': [''],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Every line needs a product and a price')
        self.assertFalse(Quote.objects.exists())

    def test_create_rejects_no_lines(self, mock_pdf):
        response = self.client.post('/quotes/dashboard/create/', {
            'company_name': 'XYZ CAFE',
            'variant_id': [''],
            'price': [''],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add at least one product line')
        self.assertFalse(Quote.objects.exists())


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class EmailQuotePDFTestCase(TestCase):
    serialized_rollback = True

    def setUp(self):
        self.user = User.objects.create_user(username='rep2', email='rep2@example.com', password='pass12345')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.quote = Quote.objects.create(company_name='XYZ CAFE')
        from django.core.files.base import ContentFile
        self.quote.pdf.save('quote_Q0001_test.pdf', ContentFile(b'%PDF-1.4 test'), save=True)

    def tearDown(self):
        self.quote.pdf.delete(save=False)

    @mock.patch('quotes.services.PostmarkClient')
    def test_emails_existing_pdf(self, mock_postmark):
        response = self.client.post(
            '/quotes/email-pdf/',
            {'email_address': 'sam@example.com', 'quote_id': self.quote.pk},
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.data)
        email = mock_postmark.return_value.emails.Email.return_value
        email.attach_binary.assert_called_once()
        email.send.assert_called_once()

    def test_missing_fields_rejected(self):
        response = self.client.post('/quotes/email-pdf/', {'quote_id': self.quote.pk}, format='json')
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/quotes/email-pdf/', {'email_address': 'a@b.c'}, format='json')
        self.assertEqual(response.status_code, 400)
