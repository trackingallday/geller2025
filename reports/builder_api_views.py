"""The report-type builder, as JSON for the admin app.

Every write validates through the same Django form the old builder pages
use (``ReportTypeForm``, ``ReportSectionForm``, ``QuestionForm``,
``QuestionOptionForm``), and every copy goes through ``builder.py``. So a
report type built in the admin app is the same shape as one built in the
old pages, and the mobile app reads both the same way.

Each write answers with the whole builder tree, not just the row that
changed: a reorder, a duplicate or a delete moves other rows too, and the
screen redraws from one source rather than patching itself.
"""
from django.db import transaction
from django.shortcuts import get_object_or_404

from chemsapp.models import Customer, Distributor
from chemsapp.staff_api import (
    error, form_data, form_errors_response, json_body, ok, staff_api,
)

from .builder import (
    OPTION_QUESTION_TYPES, PARENT_QUESTION_TYPES, ReorderError, builder_tree,
    copy_report_type_structure, copy_section_questions, duplicate_question,
    reorder, set_assignment,
)
from .forms import (
    QuestionForm, QuestionOptionForm, ReportSectionForm, ReportTypeForm,
)
from .models import (
    QUESTION_TYPES, Question, QuestionOption, ReportSection, ReportType,
    ReportTypeCustomer, ReportTypeDistributor,
)


def _fields(request, defaults):
    """The posted fields, with ``defaults`` filling any the caller left out.

    A Django form reads a missing field as empty, and a missing checkbox as
    unticked. An update that sends only the changed fields would then wipe
    the rest, so each update passes the stored values as defaults. A form
    post stays a QueryDict, so a list value keeps all its items.
    """
    data = form_data(request)
    if hasattr(data, 'getlist'):
        sent = data.copy()
        for key, value in defaults.items():
            if key not in sent:
                if isinstance(value, (list, tuple)):
                    sent.setlist(key, [str(item) for item in value])
                else:
                    sent[key] = '' if value is None else value
        return sent
    sent = dict(data)
    for key, value in defaults.items():
        sent.setdefault(key, value)
    # JSON null means "none" for a choice; the form reads that as empty.
    return {key: ('' if value is None else value) for key, value in sent.items()}


def _post_only(request):
    if request.method != 'POST':
        return error('POST required.', status=405)
    return None


def _tree(report_type):
    """The builder tree, fresh from the database after a write."""
    return ok(builder_tree(ReportType.objects.get(pk=report_type.pk)))


# --- Report types ------------------------------------------------------------

@staff_api
def builder_meta(request):
    """The fixed lists the builder's selects offer."""
    return ok({
        'question_types': [{'value': v, 'label': l} for v, l in QUESTION_TYPES],
        'parent_question_types': list(PARENT_QUESTION_TYPES),
        'option_question_types': list(OPTION_QUESTION_TYPES),
        'badge_types': [
            {'value': v, 'label': l}
            for v, l in QuestionOption._meta.get_field('badge_type').choices
        ],
        'categories': [
            {'value': v, 'label': l}
            for v, l in ReportType._meta.get_field('category').choices
        ],
    })


@staff_api
def report_type_tree(request, report_type_id):
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    return ok(builder_tree(report_type))


@staff_api
def report_type_create(request):
    refused = _post_only(request)
    if refused:
        return refused
    form = ReportTypeForm(form_data(request))
    if not form.is_valid():
        return form_errors_response(form)
    report_type = form.save(commit=False)
    report_type.created_by = request.user
    report_type.save()
    return _tree(report_type)


@staff_api
def report_type_update(request, report_type_id):
    refused = _post_only(request)
    if refused:
        return refused
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    form = ReportTypeForm(_fields(request, {
        'name': report_type.name,
        'description': report_type.description,
        'category': report_type.category,
        'auto_number_prefix': report_type.auto_number_prefix,
        'is_active': report_type.is_active,
    }), instance=report_type)
    if not form.is_valid():
        return form_errors_response(form)
    form.save()
    return _tree(report_type)


@staff_api
def report_type_delete(request, report_type_id):
    """Delete a report type.

    A report belongs to its type by a cascading key, so deleting a type
    deletes every report filled in on it. That is refused unless the caller
    says ``force``, having shown the user how many reports would go.
    """
    refused = _post_only(request)
    if refused:
        return refused
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    report_count = report_type.reports.count()
    if report_count and not json_body(request).get('force'):
        return error(
            f'{report_count} reports use this type. Deleting it deletes them too.',
            status=409, report_count=report_count)
    report_type.delete()
    return ok({'id': report_type_id, 'reports_deleted': report_count})


@staff_api
def report_type_duplicate(request, report_type_id):
    """Copy a type with its whole structure, under a new name.

    The name, prefix and other settings come from the request, falling back
    to the original's with "(Copy)" and a "C" on the prefix, as the old
    duplicate page pre-filled them.
    """
    refused = _post_only(request)
    if refused:
        return refused
    original = get_object_or_404(ReportType, pk=report_type_id)
    sent = form_data(request)
    fields = {
        'name': sent.get('name') or f'{original.name} (Copy)',
        'description': sent.get('description', original.description),
        'category': sent.get('category') or original.category,
        'auto_number_prefix': sent.get(
            'auto_number_prefix',
            f'{original.auto_number_prefix}C' if original.auto_number_prefix else ''),
        'is_active': sent.get('is_active', original.is_active),
    }
    form = ReportTypeForm(fields)
    if not form.is_valid():
        return form_errors_response(form)

    with transaction.atomic():
        copy = form.save(commit=False)
        copy.created_by = request.user
        copy.save()
        copy_report_type_structure(original, copy)
    return _tree(copy)


@staff_api
def report_type_reorder(request, report_type_id):
    """Save the order the builder's drag-and-drop arrived at.

    Body: ``{"sections": [ids], "questions": [{"section": id|null, "ids": [ids]}]}``.
    Questions are a list of groups rather than a map, because JSON object
    keys cannot be null and "no section" is a real place to be.
    """
    refused = _post_only(request)
    if refused:
        return refused
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    body = json_body(request)
    try:
        sections = [int(pk) for pk in body.get('sections', [])]
        groups = {
            (int(group['section']) if group.get('section') is not None else None):
                [int(pk) for pk in group.get('ids', [])]
            for group in body.get('questions', [])
        }
        reorder(report_type, sections, groups)
    except (TypeError, ValueError, KeyError) as exc:
        message = str(exc) if isinstance(exc, ReorderError) else 'The order could not be read.'
        return error(message)
    return _tree(report_type)


# --- Sections ----------------------------------------------------------------

@staff_api
def section_create(request, report_type_id):
    refused = _post_only(request)
    if refused:
        return refused
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    # A new section goes to the bottom unless the caller placed it.
    form = ReportSectionForm(_fields(request, {'order': report_type.sections.count()}))
    if not form.is_valid():
        return form_errors_response(form)
    section = form.save(commit=False)
    section.report_type = report_type
    section.save()
    return _tree(report_type)


@staff_api
def section_update(request, section_id):
    refused = _post_only(request)
    if refused:
        return refused
    section = get_object_or_404(ReportSection, pk=section_id)
    form = ReportSectionForm(_fields(request, {
        'name': section.name,
        'description': section.description,
        'order': section.order,
    }), instance=section)
    if not form.is_valid():
        return form_errors_response(form)
    form.save()
    return _tree(section.report_type)


@staff_api
def section_delete(request, section_id):
    """Delete a section and the questions in it (a cascading key)."""
    refused = _post_only(request)
    if refused:
        return refused
    section = get_object_or_404(ReportSection, pk=section_id)
    report_type = section.report_type
    section.delete()
    return _tree(report_type)


@staff_api
def section_duplicate(request, section_id):
    """Copy a section and its questions, just after the original."""
    refused = _post_only(request)
    if refused:
        return refused
    original = get_object_or_404(ReportSection, pk=section_id)
    sent = form_data(request)
    form = ReportSectionForm({
        'name': sent.get('name') or f'{original.name} (Copy)',
        'description': sent.get('description', original.description),
        'order': original.order + 1,
    })
    if not form.is_valid():
        return form_errors_response(form)

    with transaction.atomic():
        copy = form.save(commit=False)
        copy.report_type = original.report_type
        copy.save()
        copy_section_questions(original, copy)
    return _tree(original.report_type)


# --- Questions ---------------------------------------------------------------

def _question_form(request, report_type, instance=None):
    """A QuestionForm over the posted fields.

    On update every field defaults to its stored value, so the builder can
    send only what changed. A new question goes to the bottom of its
    section unless the caller placed it.
    """
    if instance is not None:
        defaults = {
            'question_text': instance.question_text,
            'question_type': instance.question_type,
            'section': instance.section_id,
            'help_text': instance.help_text,
            'is_required': instance.is_required,
            'order': instance.order,
            'parent_question': instance.parent_question_id,
            'show_when_parent_values': instance.get_show_when_values(),
        }
    else:
        sent_section = form_data(request).get('section') or None
        defaults = {
            'order': report_type.questions.filter(section_id=sent_section).count(),
        }
    return QuestionForm(
        _fields(request, defaults), instance=instance, report_type=report_type)


@staff_api
def question_create(request, report_type_id):
    refused = _post_only(request)
    if refused:
        return refused
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    form = _question_form(request, report_type)
    if not form.is_valid():
        return form_errors_response(form)
    question = form.save(commit=False)
    question.report_type = report_type
    question.save()
    return _tree(report_type)


@staff_api
def question_update(request, question_id):
    refused = _post_only(request)
    if refused:
        return refused
    question = get_object_or_404(Question, pk=question_id)
    form = _question_form(request, question.report_type, instance=question)
    if not form.is_valid():
        return form_errors_response(form)
    form.save()
    return _tree(question.report_type)


@staff_api
def question_delete(request, question_id):
    """Delete a question, and with it its answers in filled-in reports.

    A child question shown on this one's answer loses its condition rather
    than being deleted with it, so the child stays in the form, always
    shown.
    """
    refused = _post_only(request)
    if refused:
        return refused
    question = get_object_or_404(Question, pk=question_id)
    report_type = question.report_type
    with transaction.atomic():
        for child in question.child_questions.all():
            child.parent_question = None
            child.set_show_when_values([])
            child.save(update_fields=[
                'parent_question', 'show_when_parent_values', 'show_when_parent_value'])
        question.delete()
    return _tree(report_type)


@staff_api
def question_duplicate(request, question_id):
    refused = _post_only(request)
    if refused:
        return refused
    question = get_object_or_404(Question, pk=question_id)
    duplicate_question(question)
    return _tree(question.report_type)


# --- Options -----------------------------------------------------------------

def _option_form(request, question, instance=None):
    if instance is not None:
        defaults = {
            'text': instance.text,
            'value': instance.value,
            'is_flag': instance.is_flag,
            'badge_type': instance.badge_type,
            'additional_instructions': instance.additional_instructions,
            'order': instance.order,
        }
    else:
        defaults = {
            'order': question.options.count(),
            'badge_type': QuestionOption._meta.get_field('badge_type').default,
        }
    return QuestionOptionForm(_fields(request, defaults), request.FILES, instance=instance)


@staff_api
def option_create(request, question_id):
    refused = _post_only(request)
    if refused:
        return refused
    question = get_object_or_404(Question, pk=question_id)
    form = _option_form(request, question)
    if not form.is_valid():
        return form_errors_response(form)
    option = form.save(commit=False)
    option.question = question
    option.save()
    return _tree(question.report_type)


@staff_api
def option_update(request, option_id):
    refused = _post_only(request)
    if refused:
        return refused
    option = get_object_or_404(QuestionOption, pk=option_id)
    form = _option_form(request, option.question, instance=option)
    if not form.is_valid():
        return form_errors_response(form)
    form.save()
    return _tree(option.question.report_type)


@staff_api
def option_delete(request, option_id):
    refused = _post_only(request)
    if refused:
        return refused
    option = get_object_or_404(QuestionOption, pk=option_id)
    report_type = option.question.report_type
    option.delete()
    return _tree(report_type)


@staff_api
def option_reorder(request, question_id):
    """Body: ``{"ids": [option ids, top to bottom]}``."""
    refused = _post_only(request)
    if refused:
        return refused
    question = get_object_or_404(Question, pk=question_id)
    try:
        ids = [int(pk) for pk in json_body(request).get('ids', [])]
    except (TypeError, ValueError):
        return error('The order could not be read.')
    own = set(question.options.values_list('pk', flat=True))
    if set(ids) - own:
        return error('Those options are not on this question.')
    with transaction.atomic():
        for position, pk in enumerate(ids):
            QuestionOption.objects.filter(pk=pk).update(order=position)
    return _tree(question.report_type)


# --- Assignments -------------------------------------------------------------

@staff_api
def report_type_assignments(request, report_type_id):
    """Every customer and distributor, and whether this type is assigned to
    each. Both lists are short enough to send whole.
    """
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    customer_rows = {
        row.customer_id: row
        for row in ReportTypeCustomer.objects.filter(report_type=report_type)
    }
    distributor_rows = {
        row.distributor_id: row
        for row in ReportTypeDistributor.objects.filter(report_type=report_type)
    }

    def entry(pk, name, row):
        return {
            'id': pk,
            'name': name,
            'active': bool(row and row.is_active),
            'notes': row.notes if row else None,
        }

    return ok({
        'customers': [
            entry(c.pk, c.businessName, customer_rows.get(c.pk))
            for c in Customer.objects.order_by('businessName')
        ],
        'distributors': [
            entry(d.pk, d.businessname, distributor_rows.get(d.pk))
            for d in Distributor.objects.order_by('businessname')
        ],
    })


def _assignment_target(body):
    """The customer or distributor a toggle names, or an error response."""
    kind = body.get('kind')
    model = {'customer': Customer, 'distributor': Distributor}.get(kind)
    if model is None:
        return None, error('kind must be "customer" or "distributor".')
    try:
        return model.objects.get(pk=int(body.get('id'))), None
    except (TypeError, ValueError, model.DoesNotExist):
        return None, error(f'That {kind} does not exist.', status=404)


@staff_api
def report_type_assignment_set(request, report_type_id):
    """Body: ``{"kind": "customer"|"distributor", "id": n, "active": bool,
    "notes": "..."}``."""
    refused = _post_only(request)
    if refused:
        return refused
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    body = json_body(request)
    target, failure = _assignment_target(body)
    if failure:
        return failure
    set_assignment(report_type, target, bool(body.get('active')), request.user,
                   notes=body.get('notes'))
    return ok({'kind': body['kind'], 'id': target.pk, 'active': bool(body.get('active'))})


@staff_api
def assignment_matrix(request):
    """The customers-by-types grid of the old Assign Report Types page."""
    return ok({
        'customers': [
            {'id': c.pk, 'name': c.businessName}
            for c in Customer.objects.order_by('businessName')
        ],
        'report_types': [
            {'id': t.pk, 'name': t.name, 'category': t.category}
            for t in ReportType.objects.filter(is_active=True).order_by('name')
        ],
        'active': [
            [row['customer_id'], row['report_type_id']]
            for row in ReportTypeCustomer.objects.filter(is_active=True)
            .values('customer_id', 'report_type_id')
        ],
    })


@staff_api
def assignment_toggle(request):
    """Body: ``{"customer_id": n, "report_type_id": n, "active": bool}``."""
    refused = _post_only(request)
    if refused:
        return refused
    body = json_body(request)
    try:
        customer = Customer.objects.get(pk=int(body['customer_id']))
        report_type = ReportType.objects.get(pk=int(body['report_type_id']))
    except (KeyError, TypeError, ValueError):
        return error('customer_id and report_type_id are required.')
    except (Customer.DoesNotExist, ReportType.DoesNotExist):
        return error('Not found.', status=404)
    active = bool(body.get('active'))
    set_assignment(report_type, customer, active, request.user)
    return ok({'customer_id': customer.pk, 'report_type_id': report_type.pk, 'active': active})
