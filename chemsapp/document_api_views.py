"""JSON list, upload, edit and delete of product document versions.

Each upload is one ``ProductDocument`` row with a version and a date. The
file fields on ``Product`` and ``ProductVariant`` stay the pointer to the
current version, so an upload also sets that field. See the model for the
rules.

The send API emails download links for the SDS and the info sheet. Each
link is ``/product_download/<id>/<kind>/``, so a later click always gives
the newest file. A ``DocumentSend`` row records which version was current
at send time.
"""
import logging

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from postmarker.core import PostmarkClient

from .models import DocumentSend, DocumentSendItem, Product, ProductDocument
from .staff_api import error, form_data, form_errors_response, json_body, ok, staff_api

logger = logging.getLogger(__name__)

PRODUCT_KINDS = [ProductDocument.SDS, ProductDocument.INFO, ProductDocument.MPI_APPROVAL]


class DocumentUploadForm(forms.Form):
    kind = forms.ChoiceField(choices=ProductDocument.KIND_CHOICES)
    file = forms.FileField()
    version = forms.CharField(max_length=50, required=False)
    issued_on = forms.DateField(required=False)
    variant = forms.IntegerField(required=False)


class DocumentEditForm(forms.ModelForm):
    class Meta:
        model = ProductDocument
        fields = ['version', 'issued_on']


def _user_name(user):
    if user is None:
        return None
    return user.get_full_name() or user.username


def _serialize(document):
    """One version as JSON."""
    try:
        url = document.file.url
    except ValueError:
        url = None
    return {
        'id': document.pk,
        'kind': document.kind,
        'kind_label': document.get_kind_display(),
        'variant_id': document.variant_id,
        'file_name': document.file.name.rsplit('/', 1)[-1],
        'url': url,
        'version': document.version,
        'issued_on': document.issued_on.isoformat() if document.issued_on else None,
        'uploaded_at': document.uploaded_at.isoformat(),
        'uploaded_by': _user_name(document.uploaded_by),
        'is_current': document.is_current,
        'send_count': document.send_items.count(),
    }


def _product_documents(product):
    """All versions of a product, grouped by kind, and by size for labels."""
    rows = list(
        product.documents.select_related('uploaded_by', 'variant', 'product')
        .order_by('-uploaded_at', '-id'))
    documents = {
        kind: [_serialize(row) for row in rows if row.kind == kind and row.variant_id is None]
        for kind in PRODUCT_KINDS
    }
    labels = []
    for variant in product.variants.select_related('size').order_by('pk'):
        labels.append({
            'variant_id': variant.pk,
            'code': variant.code,
            'size': variant.size.name if variant.size_id else None,
            'versions': [
                _serialize(row) for row in rows
                if row.kind == ProductDocument.LABEL and row.variant_id == variant.pk
            ],
        })
    return {
        'product_id': product.pk,
        'documents': documents,
        'labels': labels,
        'kinds': [{'value': value, 'label': label} for value, label in ProductDocument.KIND_CHOICES],
    }


@staff_api
@require_http_methods(['GET', 'POST'])
def product_document_list(request, product_id):
    """GET: every version of the product's documents and size labels.
    POST (multipart): upload a new version. It becomes the current one."""
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'GET':
        return ok(_product_documents(product))

    form = DocumentUploadForm(form_data(request), request.FILES)
    if not form.is_valid():
        return form_errors_response(form)
    kind = form.cleaned_data['kind']
    variant = None
    if kind == ProductDocument.LABEL:
        variant_id = form.cleaned_data['variant']
        if not variant_id:
            return error('A label needs a size.', errors={'variant': ['Select a size.']})
        variant = product.variants.filter(pk=variant_id).first()
        if variant is None:
            return error('This size is not on the product.', errors={'variant': ['Unknown size.']})

    with transaction.atomic():
        # Make the row first. The post_save signal of the owner then finds
        # it and makes no duplicate.
        document = ProductDocument(
            product=product, variant=variant, kind=kind,
            version=form.cleaned_data['version'] or '',
            issued_on=form.cleaned_data['issued_on'],
            uploaded_by=request.user,
        )
        document.file.save(form.cleaned_data['file'].name, form.cleaned_data['file'], save=True)
        owner = variant if variant is not None else product
        field = ProductDocument.POINTER_FIELDS[kind]
        setattr(owner, field, document.file.name)
        owner.save(update_fields=[field])
    return ok(_serialize(document))


@staff_api
@require_http_methods(['POST', 'DELETE'])
def product_document_detail(request, document_id):
    """POST: change the version or the date (partial).
    DELETE: remove an old version. The current version cannot be removed."""
    document = get_object_or_404(
        ProductDocument.objects.select_related('product', 'variant', 'uploaded_by'), pk=document_id)

    if request.method == 'DELETE':
        if document.is_current:
            return error(
                'This is the current version. Upload a new version first.', status=409)
        # The file stays in storage. Another row or an old email link can
        # still name it.
        document.delete()
        return ok({'id': document_id})

    data = form_data(request)
    merged = {'version': document.version, 'issued_on': document.issued_on}
    merged.update({key: data[key] for key in ('version', 'issued_on') if key in data})
    form = DocumentEditForm(merged, instance=document)
    if not form.is_valid():
        return form_errors_response(form)
    return ok(_serialize(form.save()))


# ---------------------------------------------------------------------------
# Send documents by email
# ---------------------------------------------------------------------------

SEND_KINDS = [ProductDocument.SDS, ProductDocument.INFO]
SEND_KIND_LABELS = {ProductDocument.SDS: 'Safety data sheet', ProductDocument.INFO: 'Product information sheet'}
MAX_RECIPIENTS = 20
RECENT_SENDS = 50


def _serialize_send(send):
    return {
        'id': send.pk,
        'recipients': send.recipients,
        'message': send.message,
        'sent_by': _user_name(send.sent_by),
        'sent_at': send.sent_at.isoformat(),
        'items': [{
            'product_id': item.product_id,
            'product_name': item.product_name,
            'kind': item.kind,
            'kind_label': SEND_KIND_LABELS.get(item.kind, item.kind),
            'document_id': item.document_id,
            'version': item.document.version if item.document else '',
            'issued_on': (item.document.issued_on.isoformat()
                          if item.document and item.document.issued_on else None),
        } for item in send.items.all()],
    }


def _clean_emails(raw):
    """Return (emails, errors). The emails are lower case, with no duplicates."""
    if not isinstance(raw, list):
        return [], ['Give a list of email addresses.']
    emails, errors = [], []
    for value in raw:
        email = str(value or '').strip().lower()
        if not email:
            continue
        try:
            validate_email(email)
        except ValidationError:
            errors.append(f'"{email}" is not a valid email address.')
            continue
        if email not in emails:
            emails.append(email)
    if not emails and not errors:
        errors.append('Give at least one email address.')
    if len(emails) > MAX_RECIPIENTS:
        errors.append(f'Send to {MAX_RECIPIENTS} addresses or fewer.')
    return emails, errors


def _clean_items(raw):
    """Return (lines, errors). Each line is (product, kind)."""
    if not isinstance(raw, list) or not raw:
        return [], ['Select at least one product.']
    ids = []
    for item in raw:
        if isinstance(item, dict) and str(item.get('product', '')).isdigit():
            ids.append(int(item['product']))
    products = Product.objects.in_bulk(ids)
    lines, errors = [], []
    for item in raw:
        if not isinstance(item, dict):
            errors.append('Each item needs a product and kinds.')
            continue
        product = products.get(int(item['product'])) if str(item.get('product', '')).isdigit() else None
        if product is None:
            errors.append(f'Product {item.get("product")} does not exist.')
            continue
        kinds = item.get('kinds') or []
        if not isinstance(kinds, list) or not kinds:
            errors.append(f'{product.name}: select SDS, info sheet, or both.')
            continue
        for kind in kinds:
            if kind not in SEND_KINDS:
                errors.append(f'{product.name}: "{kind}" cannot be sent.')
                continue
            current = getattr(product, ProductDocument.POINTER_FIELDS[kind])
            if not current or not current.name:
                errors.append(f'{product.name} has no {SEND_KIND_LABELS[kind].lower()}.')
                continue
            if (product, kind) not in lines:
                lines.append((product, kind))
    return lines, errors


def _email_body(request, message, lines):
    parts = []
    if message.strip():
        parts.append(message.strip())
        parts.append('')
    current_name = None
    for product, kind in lines:
        if product.name != current_name:
            if current_name is not None:
                parts.append('')
            parts.append(product.name)
            current_name = product.name
        url = request.build_absolute_uri(reverse('product_download', args=[product.pk, kind]))
        parts.append(f'{SEND_KIND_LABELS[kind]}: {url}')
    parts.append('')
    parts.append('Each link always gives the newest version of the document.')
    parts.append('')
    parts.append('Geller Chemicals')
    return '\n'.join(parts)


def _send_one(email, subject, body, reply_to):
    """Send one email through Postmark. Errors go to the caller."""
    postmark = PostmarkClient(server_token=settings.POSTMARK_SERVER_API_TOKEN)
    postmark.emails.Email(
        From='noreply@geller.co.nz', To=email, Subject=subject,
        TextBody=body, ReplyTo=reply_to,
    ).send()


def _current_document(product, kind):
    """The ProductDocument row of the file that is current now, or None."""
    current = getattr(product, ProductDocument.POINTER_FIELDS[kind])
    return (ProductDocument.objects
            .filter(product=product, variant=None, kind=kind, file=current.name)
            .order_by('-id').first())


@staff_api
@require_http_methods(['GET', 'POST'])
def document_send_list(request):
    """GET: the recent sends, newest first. ``?product=<id>`` and ``?q=``
    (part of an email address) filter the list.

    POST (JSON): ``{emails: [...], items: [{product, kinds: ["sds", "info"]}],
    message}``. Sends one email to each address. Each recipient sees only
    their own address.
    """
    if request.method == 'GET':
        sends = DocumentSend.objects.select_related('sent_by').prefetch_related('items__document')
        product_id = request.GET.get('product', '')
        if product_id.isdigit():
            sends = sends.filter(items__product_id=int(product_id)).distinct()
        q = request.GET.get('q', '').strip().lower()
        if q:
            sends = sends.filter(recipients__icontains=q)
        return ok([_serialize_send(send) for send in sends[:RECENT_SENDS]])

    data = json_body(request)
    if not isinstance(data, dict):
        return error('Send a JSON object.')
    emails, email_errors = _clean_emails(data.get('emails'))
    lines, item_errors = _clean_items(data.get('items'))
    message = str(data.get('message') or '')
    if email_errors or item_errors:
        errors = {}
        if email_errors:
            errors['emails'] = email_errors
        if item_errors:
            errors['items'] = item_errors
        return error('The email was not sent. Correct the fields.', errors=errors)

    subject = 'Product documents from Geller Chemicals'
    body = _email_body(request, message, lines)
    reply_to = request.user.email or settings.EMAIL_ADMIN
    sent, failed = [], []
    for email in emails:
        try:
            _send_one(email, subject, body, reply_to)
            sent.append(email)
        except Exception as exc:  # Postmark raises many kinds of errors.
            logger.error('Document send to %s failed: %s', email, exc)
            failed.append(email)
    if not sent:
        return error('The email service did not send the email. Try again later.',
                     status=502, failed=failed)

    with transaction.atomic():
        send = DocumentSend.objects.create(recipients=sent, message=message, sent_by=request.user)
        DocumentSendItem.objects.bulk_create([
            DocumentSendItem(send=send, product=product, product_name=product.name,
                             kind=kind, document=_current_document(product, kind))
            for product, kind in lines
        ])
    send = (DocumentSend.objects.select_related('sent_by')
            .prefetch_related('items__document').get(pk=send.pk))
    return ok(_serialize_send(send), failed=failed)
