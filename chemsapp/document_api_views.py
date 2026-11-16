"""JSON list, upload, edit and delete of product document versions.

Each upload is one ``ProductDocument`` row with a version and a date. The
file fields on ``Product`` and ``ProductVariant`` stay the pointer to the
current version, so an upload also sets that field. See the model for the
rules.
"""
from django import forms
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import Product, ProductDocument
from .staff_api import error, form_data, form_errors_response, ok, staff_api

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
