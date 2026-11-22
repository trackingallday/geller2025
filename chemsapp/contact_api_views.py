"""JSON list of website contacts for the admin app.

A website contact is a ``Contact`` row. The website makes one for each
Contact Us enquiry (``create_contact``) and for each SDS download
(``sds_enquire``). Before this API, staff saw these rows only in ``/admin/``.
"""
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import Contact
from .staff_api import error, json_body, ok, search_q, staff_api
from .workflow_api_views import _page, _when

SDS_PREFIX = 'Downloaded SDS for product:'
SEARCH_FIELDS = ['nameFrom', 'emailFrom', 'companyName', 'distributorName', 'content']


def _serialize(contact):
    """One contact as JSON.

    An SDS row from before the ``product`` field has no link. For that row,
    the product name comes from the ``content`` text.
    """
    is_sds = contact.isSDSDownload
    product_name = None
    if contact.product_id:
        product_name = contact.product.name
    elif is_sds and contact.content.startswith(SDS_PREFIX):
        product_name = contact.content[len(SDS_PREFIX):].strip() or None
    return {
        'id': contact.pk,
        'name': contact.nameFrom,
        'company': contact.companyName or '',
        'distributor': contact.distributorName or '',
        'email': contact.emailFrom,
        'created_at': _when(contact.created_at),
        'kind': 'sds' if is_sds else 'enquiry',
        'product_id': contact.product_id,
        'product_name': product_name,
        'message': '' if is_sds else contact.content,
        'replied': contact.replied,
    }


@staff_api
@require_http_methods(['GET'])
def contact_list(request):
    """GET: one page of website contacts, newest first.

    Filters: ``q`` (search), ``kind`` (``sds`` or ``enquiry``) and
    ``replied`` (``0`` or ``1``).
    """
    queryset = Contact.objects.select_related('product').order_by('-created_at', '-pk')
    search = request.GET.get('q', '').strip()
    if search:
        queryset = queryset.filter(search_q(search, SEARCH_FIELDS))
    kind = request.GET.get('kind', '')
    if kind == 'sds':
        queryset = queryset.filter(isSDSDownload=True)
    elif kind == 'enquiry':
        queryset = queryset.filter(isSDSDownload=False)
    replied = request.GET.get('replied', '')
    if replied in ('0', '1'):
        queryset = queryset.filter(replied=replied == '1')

    rows, pager = _page(queryset, request)
    return ok({'contacts': [_serialize(row) for row in rows], **pager})


@staff_api
@require_http_methods(['GET', 'PATCH'])
def contact_detail(request, contact_id):
    """GET: one contact. PATCH: set ``replied``. No other field can change."""
    contact = get_object_or_404(Contact.objects.select_related('product'), pk=contact_id)
    if request.method == 'PATCH':
        body = json_body(request)
        if not isinstance(body.get('replied'), bool):
            return error('Send "replied" as true or false.')
        contact.replied = body['replied']
        contact.save(update_fields=['replied', 'updated_at'])
    return ok(_serialize(contact))
