import base64
import html as html_module
import io
import os

import pyqrcode
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from chemsapp.models import Customer, Product
from chemsapp.wall_chart_colors import row_colors


def _build_wall_chart_pdf(customer, products, base_url):
    """Build and return PDF bytes for a wall chart given a customer and product queryset."""
    product_rows = []
    for product in products:
        qr_code = None
        if product.sdsSheet:
            link = 'http://geller.co.nz' + product.sdsSheet.url
            qr_url = pyqrcode.create(link)
            buf = io.BytesIO()
            qr_url.svg(buf)
            encoded = base64.b64encode(buf.getvalue()).decode()
            qr_code = 'data:image/svg+xml;base64,' + encoded

        description = html_module.unescape(strip_tags(product.application))
        directions = html_module.unescape(strip_tags(product.procedure))

        stripe_color, tint_color = row_colors(product.wall_chart_color)

        ppe_items = []
        for wear in product.safetyWears.all():
            if wear.imageLink:
                icon_url = f'file://{wear.imageLink.path}'
                ppe_items.append({'name': wear.name, 'url': icon_url})

        product_rows.append({
            'product': product,
            'qr_code': qr_code,
            'description': description,
            'directions': directions,
            'stripe_color': stripe_color,
            'tint_color': tint_color,
            'ppe_items': ppe_items,
        })

    geller_logo = os.path.join(settings.BASE_DIR, 'reports/static/reports/img/report-logo.png')
    if not os.path.exists(geller_logo):
        geller_logo = os.path.join(settings.STATIC_ROOT or '', 'reports/img/report-logo.png')
    geller_logo_url = f'file://{geller_logo}' if os.path.exists(geller_logo) else None

    html_string = render_to_string('chemsapp/wall_chart_pdf.html', {
        'customer': customer,
        'product_rows': product_rows,
        'geller_logo': geller_logo_url,
        'base_url': base_url,
    })

    font_config = FontConfiguration()
    pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf(font_config=font_config)
    return pdf_bytes


@csrf_exempt
@api_view(['GET'])
def wall_chart_pdf(request):
    """
    GET /wall_chart_pdf/?customer_id=<id>&product_ids=1,2,3
    Also accepts product_variant_ids=1,2,3 (resolves to parent products, deduped).
    Returns a PDF wall chart for the given customer and products.
    Auth: DRF Token (Authorization: Token <key>)
    """
    from chemsapp.models import ProductVariant

    customer_id = request.query_params.get('customer_id')
    product_ids_param = request.query_params.get('product_ids', '')
    variant_ids_param = request.query_params.get('product_variant_ids', '')

    if not customer_id:
        return JsonResponse({'error': 'customer_id is required'}, status=400)

    customer = get_object_or_404(Customer, pk=customer_id)

    product_ids = [int(x) for x in product_ids_param.split(',') if x.strip().isdigit()]
    variant_ids = [int(x) for x in variant_ids_param.split(',') if x.strip().isdigit()]

    if variant_ids:
        seen = set()
        ordered_product_ids = []
        for v in ProductVariant.objects.filter(pk__in=variant_ids).select_related('product').order_by('id'):
            if v.product_id not in seen:
                seen.add(v.product_id)
                ordered_product_ids.append(v.product_id)
        product_ids = ordered_product_ids

    if not product_ids:
        return JsonResponse({'error': 'product_ids or product_variant_ids is required'}, status=400)

    products_by_id = {
        p.pk: p
        for p in Product.objects.filter(pk__in=product_ids).prefetch_related('safetyWears')
    }
    products = [products_by_id[pid] for pid in product_ids if pid in products_by_id]

    pdf_bytes = _build_wall_chart_pdf(customer, products, request.build_absolute_uri('/'))
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="wall-chart-{customer_id}.pdf"'
    return response
