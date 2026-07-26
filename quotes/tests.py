import tempfile
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from chemsapp.models import FillType, Product, ProductVariant, VariantFillOverride
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


def make_variant(product, **kwargs):
    defaults = dict(code='CONQUEST20', pack_size=1, barcode='9400000000001')
    defaults.update(kwargs)
    return ProductVariant.objects.create(product=product, **defaults)


class FillOptionsTestCase(TestCase):
    serialized_rollback = True

    def setUp(self):
        self.bucket = FillType.objects.create(name='Bucket Fill', volume_litres=Decimal('10'), sort_order=1)
        self.spray = FillType.objects.create(name='Spray Bottle', volume_litres=Decimal('0.5'), sort_order=2)
        self.product = make_product(dilution_ratio=Decimal('100'))
        self.product.fill_types.set([self.bucket, self.spray])
        self.variant = make_variant(self.product, volume_litres=Decimal('20'))

    def test_computed_fills(self):
        options = self.variant.get_fill_options()
        self.assertEqual(len(options), 2)
        bucket = next(o for o in options if o['fill_type'] == self.bucket)
        spray = next(o for o in options if o['fill_type'] == self.spray)
        # 20L × 100 ÷ 10L = 200 bucket fills; ÷ 0.5L = 4000 spray fills
        self.assertEqual(bucket['fills'], Decimal('200.00'))
        self.assertEqual(bucket['source'], 'computed')
        self.assertEqual(spray['fills'], Decimal('4000.00'))

    def test_override_beats_computed(self):
        VariantFillOverride.objects.create(variant=self.variant, fill_type=self.bucket, fills=Decimal('300'))
        options = self.variant.get_fill_options()
        bucket = next(o for o in options if o['fill_type'] == self.bucket)
        self.assertEqual(bucket['fills'], Decimal('300'))
        self.assertEqual(bucket['source'], 'override')

    def test_override_only_for_non_liquid_product(self):
        # 4KG powder: no dilution, no volume — only the override produces a line
        powder = make_product(name='Powder', productCode='POWDER4')
        powder_variant = make_variant(powder, code='POWDER4KG', barcode='9400000000002')
        VariantFillOverride.objects.create(variant=powder_variant, fill_type=self.bucket, fills=Decimal('80'))
        options = powder_variant.get_fill_options()
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]['fills'], Decimal('80'))
        self.assertEqual(options[0]['source'], 'override')

    def test_no_data_gives_empty_list(self):
        bare = make_product(name='Bare', productCode='BARE')
        bare_variant = make_variant(bare, code='BARE1', barcode='9400000000003')
        self.assertEqual(bare_variant.get_fill_options(), [])

    def test_missing_volume_skips_computed(self):
        self.variant.volume_litres = None
        self.variant.save()
        self.assertEqual(self.variant.get_fill_options(), [])

    def test_inactive_fill_type_excluded(self):
        self.spray.is_active = False
        self.spray.save()
        options = self.variant.get_fill_options()
        self.assertEqual([o['fill_type'] for o in options], [self.bucket])


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
        bucket = FillType.objects.create(name='Bucket Fill', volume_litres=Decimal('10'))
        product = make_product(dilution_ratio=Decimal('100'))
        product.fill_types.set([bucket])
        variant = make_variant(product, volume_litres=Decimal('20'))
        snapshot = build_cost_in_use_snapshot(variant, Decimal('89.90'))
        self.assertEqual(snapshot, [{
            'fill_type': 'Bucket Fill',
            'fills': '200.00',
            'cost': '0.45',
            'display': 'Bucket Fill .45c',
        }])


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

        self.bucket = FillType.objects.create(name='Bucket Fill', volume_litres=Decimal('10'))
        self.product = make_product(dilution_ratio=Decimal('100'))
        self.product.fill_types.set([self.bucket])
        self.variant = make_variant(self.product, volume_litres=Decimal('20'))

    def _payload(self, **overrides):
        payload = {
            'company_name': 'XYZ CAFE',
            'address': '29 BRIDGE ST\nCAMBRIDGE',
            'contact_name': 'Sam Brown',
            'lines': [{'product_variant_id': self.variant.pk, 'price': '89.90'}],
        }
        payload.update(overrides)
        return payload

    def test_submit_creates_quote_with_snapshots(self, mock_pdf):
        response = self.client.post('/quotes/submit/', self._payload(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['quote_number'], 'Q0001')
        self.assertEqual(response.data['company_name'], 'XYZ CAFE')

        line = QuoteLine.objects.get()
        self.assertEqual(line.product_name, 'Conquest Dishwash Detergent')
        self.assertEqual(line.product_code, 'CONQUEST20')
        # RichText HTML stripped from the description snapshot
        self.assertNotIn('<', line.description)
        self.assertEqual(line.cost_in_use[0]['display'], 'Bucket Fill .45c')
        mock_pdf.assert_called_once()

    def test_snapshot_frozen_against_product_changes(self, mock_pdf):
        self.client.post('/quotes/submit/', self._payload(), format='json')
        self.product.dilution_ratio = Decimal('50')
        self.product.save()
        line = QuoteLine.objects.get()
        self.assertEqual(line.cost_in_use[0]['cost'], '0.45')  # unchanged

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

    def test_catalogue_lists_all_variants_with_fill_options(self, mock_pdf):
        response = self.client.get('/quotes/catalogue/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        item = response.data[0]
        self.assertEqual(item['code'], 'CONQUEST20')
        self.assertEqual(item['fill_options'][0]['fills'], '200.00')

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

        self.bucket = FillType.objects.create(name='Bucket Fill', volume_litres=Decimal('10'))
        self.product = make_product(dilution_ratio=Decimal('100'))
        self.product.fill_types.set([self.bucket])
        self.variant = make_variant(self.product, volume_litres=Decimal('20'))

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

    def test_create_quote_via_form(self, mock_pdf):
        response = self.client.post('/quotes/dashboard/create/', {
            'company_name': 'XYZ CAFE',
            'address': '29 BRIDGE ST\nCAMBRIDGE',
            'contact_name': 'Sam Brown',
            'customer_id': '',
            'variant_id': [str(self.variant.pk)],
            'price': ['89.90'],
        })
        self.assertEqual(response.status_code, 302)
        quote = Quote.objects.get()
        self.assertEqual(quote.company_name, 'XYZ CAFE')
        self.assertEqual(quote.created_by, self.user)
        line = quote.lines.get()
        self.assertEqual(line.cost_in_use[0]['display'], 'Bucket Fill .45c')
        mock_pdf.assert_called_once()

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
