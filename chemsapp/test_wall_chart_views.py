from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, Client
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from chemsapp.models import Customer, Product, SafetyWear


def make_user(username='testuser', is_staff=False, is_superuser=False):
    return User.objects.create_user(
        username=username,
        email=f'{username}@test.com',
        password='testpass123',
        is_staff=is_staff,
        is_superuser=is_superuser,
    )


def make_customer(user):
    return Customer.objects.create(
        user=user,
        businessName='Test Business',
        phoneNumber='555-1234',
        address='1 Test St',
    )


def make_product(name='Test Product', code='TP001', color='#aaddff'):
    return Product.objects.create(
        name=name,
        productCode=code,
        brand='TestBrand',
        description='<p>A test product</p>',
        directions='<p>Use carefully</p>',
        wall_chart_color=color,
    )


FAKE_PDF = b'%PDF-fake'


class WallChartPdfAPIViewTests(TestCase):
    serialized_rollback = True
    def setUp(self):
        self.client = APIClient()
        self.user = make_user('apiuser')
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.customer = make_customer(self.user)
        self.product = make_product()
        self.customer.products.add(self.product)

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    @patch('chemsapp.wall_chart_views._build_wall_chart_pdf', return_value=FAKE_PDF)
    def test_returns_pdf(self, mock_build):
        self._auth()
        response = self.client.get(
            '/wall_chart_pdf/',
            {'customer_id': self.customer.pk, 'product_ids': str(self.product.pk)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response.content, FAKE_PDF)
        mock_build.assert_called_once()

    @patch('chemsapp.wall_chart_views._build_wall_chart_pdf', return_value=FAKE_PDF)
    def test_content_disposition_includes_customer_id(self, mock_build):
        self._auth()
        response = self.client.get(
            '/wall_chart_pdf/',
            {'customer_id': self.customer.pk, 'product_ids': str(self.product.pk)},
        )
        self.assertIn(str(self.customer.pk), response['Content-Disposition'])

    def test_requires_authentication(self):
        response = self.client.get(
            '/wall_chart_pdf/',
            {'customer_id': self.customer.pk, 'product_ids': str(self.product.pk)},
        )
        self.assertEqual(response.status_code, 401)

    def test_missing_customer_id_returns_400(self):
        self._auth()
        response = self.client.get('/wall_chart_pdf/', {'product_ids': str(self.product.pk)})
        self.assertEqual(response.status_code, 400)

    def test_missing_product_ids_returns_400(self):
        self._auth()
        response = self.client.get('/wall_chart_pdf/', {'customer_id': self.customer.pk})
        self.assertEqual(response.status_code, 400)

    def test_unknown_customer_returns_404(self):
        self._auth()
        response = self.client.get('/wall_chart_pdf/', {'customer_id': 99999, 'product_ids': '1'})
        self.assertEqual(response.status_code, 404)

    @patch('chemsapp.wall_chart_views._build_wall_chart_pdf', return_value=FAKE_PDF)
    def test_product_variant_ids_resolved(self, mock_build):
        """product_variant_ids param should resolve to parent products."""
        from chemsapp.models import ProductVariant
        variant = ProductVariant.objects.create(
            product=self.product,
            pack_size=1,
            barcode='BAR001',
        )
        self._auth()
        response = self.client.get(
            '/wall_chart_pdf/',
            {'customer_id': self.customer.pk, 'product_variant_ids': str(variant.pk)},
        )
        self.assertEqual(response.status_code, 200)
        _, called_products, _ = mock_build.call_args[0]
        self.assertIn(self.product, list(called_products))


class WallChartAdminViewTests(TestCase):
    serialized_rollback = True
    def setUp(self):
        self.client = Client()
        self.admin_user = make_user('adminuser', is_staff=True, is_superuser=True)
        self.customer_user = make_user('custuser')
        self.customer = make_customer(self.customer_user)
        self.product = make_product()
        self.customer.products.add(self.product)

    def _login(self):
        self.client.login(username='adminuser', password='testpass123')

    @patch('chemsapp.wall_chart_views._build_wall_chart_pdf', return_value=FAKE_PDF)
    def test_returns_pdf(self, mock_build):
        self._login()
        response = self.client.get(f'/admin/chemsapp/customer/{self.customer.pk}/wall-chart/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response.content, FAKE_PDF)

    @patch('chemsapp.wall_chart_views._build_wall_chart_pdf', return_value=FAKE_PDF)
    def test_passes_all_customer_products(self, mock_build):
        second_product = make_product('Second Product', 'SP002', '#ffddaa')
        self.customer.products.add(second_product)
        self._login()
        self.client.get(f'/admin/chemsapp/customer/{self.customer.pk}/wall-chart/')
        _, called_products, _ = mock_build.call_args[0]
        product_pks = {p.pk for p in called_products}
        self.assertIn(self.product.pk, product_pks)
        self.assertIn(second_product.pk, product_pks)

    def test_requires_admin_login(self):
        response = self.client.get(f'/admin/chemsapp/customer/{self.customer.pk}/wall-chart/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_non_staff_cannot_access(self):
        self.client.login(username='custuser', password='testpass123')
        response = self.client.get(f'/admin/chemsapp/customer/{self.customer.pk}/wall-chart/')
        self.assertEqual(response.status_code, 302)

    @patch('chemsapp.wall_chart_views._build_wall_chart_pdf', return_value=FAKE_PDF)
    def test_unknown_customer_returns_404(self, mock_build):
        self._login()
        response = self.client.get('/admin/chemsapp/customer/99999/wall-chart/')
        self.assertEqual(response.status_code, 404)


class BuildWallChartPdfTests(TestCase):
    serialized_rollback = True
    """Unit tests for the _build_wall_chart_pdf helper."""

    def setUp(self):
        self.customer_user = make_user('builduser')
        self.customer = make_customer(self.customer_user)
        self.product = make_product()

    @patch('chemsapp.wall_chart_views.HTML')
    def test_returns_bytes(self, mock_html_cls):
        mock_html_cls.return_value.write_pdf.return_value = FAKE_PDF
        from chemsapp.wall_chart_views import _build_wall_chart_pdf
        result = _build_wall_chart_pdf(self.customer, [self.product], 'http://localhost/')
        self.assertEqual(result, FAKE_PDF)

    @patch('chemsapp.wall_chart_views.HTML')
    def test_tint_color_passed_to_template(self, mock_html_cls):
        mock_html_cls.return_value.write_pdf.return_value = FAKE_PDF
        from chemsapp.wall_chart_views import _build_wall_chart_pdf
        with patch('chemsapp.wall_chart_views.render_to_string', return_value='<html/>') as mock_render:
            _build_wall_chart_pdf(self.customer, [self.product], 'http://localhost/')
            _, ctx = mock_render.call_args[0]
            row = ctx['product_rows'][0]
            self.assertIn('tint_color', row)
            self.assertIn('stripe_color', row)
            self.assertIn('ppe_items', row)

    @patch('chemsapp.wall_chart_views.HTML')
    def test_ppe_items_built_from_safetywears(self, mock_html_cls):
        mock_html_cls.return_value.write_pdf.return_value = FAKE_PDF
        wear = SafetyWear.objects.create(name='Gloves', imageLink='icons/gloves-icon.svg')
        self.product.safetyWears.add(wear)
        from chemsapp.wall_chart_views import _build_wall_chart_pdf
        with patch('chemsapp.wall_chart_views.render_to_string', return_value='<html/>') as mock_render:
            with patch('os.path.exists', return_value=False):
                _build_wall_chart_pdf(self.customer, [self.product], 'http://localhost/')
            _, ctx = mock_render.call_args[0]
            ppe_items = ctx['product_rows'][0]['ppe_items']
            self.assertEqual(len(ppe_items), 1)
            self.assertEqual(ppe_items[0]['name'], 'Gloves')

    @patch('chemsapp.wall_chart_views.HTML')
    def test_invalid_color_uses_fallback(self, mock_html_cls):
        mock_html_cls.return_value.write_pdf.return_value = FAKE_PDF
        # Use update() to bypass the VARCHAR(7) field constraint
        Product.objects.filter(pk=self.product.pk).update(wall_chart_color='#xyz')
        self.product.refresh_from_db()
        from chemsapp.wall_chart_views import _build_wall_chart_pdf
        with patch('chemsapp.wall_chart_views.render_to_string', return_value='<html/>') as mock_render:
            _build_wall_chart_pdf(self.customer, [self.product], 'http://localhost/')
            _, ctx = mock_render.call_args[0]
            row = ctx['product_rows'][0]
            self.assertEqual(row['stripe_color'], '#aaaaaa')
            self.assertEqual(row['tint_color'], '#f5f5f5')
