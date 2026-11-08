"""JSON list, create, update and delete of application types for the admin app.

These replace the list and change pages of ``ApplicationTypeAdmin``. The
dilutions XLSX import stays in ``/admin/``.
"""
from django import forms
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import ApplicationType
from .staff_api import error, form_data, form_errors_response, ok, search_q, staff_api


class ApplicationTypeForm(forms.ModelForm):
    class Meta:
        model = ApplicationType
        fields = [
            'name', 'category', 'value_kind', 'unit_volume_litres',
            'unit_label', 'sort_order', 'is_active',
        ]


def _serialize(application_type):
    """One application type as JSON. The decimal is a string, so no precision is lost."""
    volume = application_type.unit_volume_litres
    return {
        'id': application_type.pk,
        'name': application_type.name,
        'category': application_type.category,
        'value_kind': application_type.value_kind,
        'value_kind_label': application_type.get_value_kind_display(),
        'unit_volume_litres': None if volume is None else str(volume),
        'unit_label': application_type.unit_label,
        'sort_order': application_type.sort_order,
        'is_active': application_type.is_active,
        'dilution_count': application_type.dilutions.count(),
    }


def _bound_form(request, instance=None):
    """A form bound to the posted fields.

    For an update, a field that the caller did not send keeps its stored
    value. As a result, the list can send only ``sort_order`` or ``is_active``.
    """
    data = form_data(request)
    if instance is not None:
        merged = {
            name: getattr(instance, name)
            for name in ApplicationTypeForm._meta.fields
        }
        # Without this merge, a BooleanField reads a missing key as False.
        merged.update(dict(data.items()))
        data = merged
    return ApplicationTypeForm(data, instance=instance)


@staff_api
@require_http_methods(['GET', 'POST'])
def application_type_list(request):
    """GET: every application type, with an optional ``q`` search.
    POST: create one application type."""
    if request.method == 'POST':
        form = _bound_form(request)
        if not form.is_valid():
            return form_errors_response(form)
        return ok(_serialize(form.save()))

    queryset = ApplicationType.objects.all()
    search = request.GET.get('q', '').strip()
    if search:
        queryset = queryset.filter(search_q(search, ['name', 'category', 'unit_label']))
    return ok({
        'application_types': [_serialize(item) for item in queryset],
        'value_kinds': [
            {'value': value, 'label': label}
            for value, label in ApplicationType.VALUE_KIND_CHOICES
        ],
    })


@staff_api
@require_http_methods(['GET', 'POST', 'DELETE'])
def application_type_detail(request, application_type_id):
    """GET: one application type. POST: update it. DELETE: remove it."""
    application_type = get_object_or_404(ApplicationType, pk=application_type_id)

    if request.method == 'DELETE':
        try:
            application_type.delete()
        except ProtectedError:
            return error(
                'This application type has dilution rates. '
                'Set it to inactive instead.',
                status=409,
            )
        return ok({'id': application_type_id})

    if request.method == 'POST':
        form = _bound_form(request, instance=application_type)
        if not form.is_valid():
            return form_errors_response(form)
        return ok(_serialize(form.save()))

    return ok(_serialize(application_type))
