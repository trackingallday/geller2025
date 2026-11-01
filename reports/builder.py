"""The report-type builder's operations, shared by both of its front ends.

The Django builder pages (``views.py``) and the admin app's JSON API
(``staff_api_views.py``) both copy, reorder and read report types. The copy
logic lived inside the views, written out twice. Here it is written once, so
a copy made from either screen comes out the same.
"""
from django.db import transaction
from django.db.models import Count

from .models import (
    Question, QuestionOption, ReportSection, ReportTypeCustomer,
    ReportTypeDistributor,
)

# A question that can drive another's visibility. Its answers are a fixed
# set of values, which a child question's show-when list picks from.
PARENT_QUESTION_TYPES = ('yesno', 'select', 'radio', 'checkbox')

# Question types whose answers come from options.
OPTION_QUESTION_TYPES = ('select', 'radio', 'checkbox')


def _copy_options(old_question, new_question):
    """Copy every option of one question onto another.

    The attached PDF is not copied: two options would then share one stored
    file, and deleting either would remove it from both.
    """
    QuestionOption.objects.bulk_create([
        QuestionOption(
            question=new_question,
            text=option.text,
            value=option.value,
            is_flag=option.is_flag,
            badge_type=option.badge_type,
            additional_instructions=option.additional_instructions,
            order=option.order,
        )
        for option in old_question.options.all()
    ])


def _copy_questions(questions, report_type, section_for):
    """Copy questions, then rebuild the parent links among the copies.

    ``section_for(old_question)`` gives each copy its section. A parent link
    is kept only when the parent was copied too; a link to a question left
    behind would cross into the original structure. Returns the old-id to
    new-question mapping.
    """
    questions = list(questions)
    mapping = {}
    for old in questions:
        mapping[old.pk] = Question.objects.create(
            report_type=report_type,
            section=section_for(old),
            question_text=old.question_text,
            question_type=old.question_type,
            help_text=old.help_text,
            is_required=old.is_required,
            order=old.order,
        )

    for old in questions:
        new = mapping[old.pk]
        parent = mapping.get(old.parent_question_id)
        if parent is not None:
            new.parent_question = parent
            new.set_show_when_values(old.get_show_when_values())
            new.save(update_fields=[
                'parent_question', 'show_when_parent_values', 'show_when_parent_value'])
        _copy_options(old, new)

    return mapping


@transaction.atomic
def copy_report_type_structure(original, new_report_type):
    """Copy every section, question and option of one type into another.

    ``new_report_type`` is already saved, with its own name and prefix.
    Returns ``(section_count, question_count)``.
    """
    sections = {
        old.pk: ReportSection.objects.create(
            report_type=new_report_type,
            name=old.name,
            description=old.description,
            order=old.order,
        )
        for old in original.sections.all()
    }
    questions = _copy_questions(
        original.questions.all(), new_report_type,
        lambda old: sections.get(old.section_id))
    return len(sections), len(questions)


@transaction.atomic
def copy_section_questions(original_section, new_section):
    """Copy the questions of one section into another. Returns the count."""
    questions = _copy_questions(
        original_section.questions.all(), original_section.report_type,
        lambda old: new_section)
    return len(questions)


@transaction.atomic
def duplicate_question(original):
    """A copy of one question, placed just after it, options included.

    The copy keeps the original's parent and show-when values: a duplicate
    of a conditional question should show under the same condition.
    """
    copy = Question.objects.create(
        report_type=original.report_type,
        section=original.section,
        question_text=original.question_text,
        question_type=original.question_type,
        help_text=original.help_text,
        is_required=original.is_required,
        order=original.order + 1,
        parent_question=original.parent_question,
    )
    if original.parent_question_id:
        copy.set_show_when_values(original.get_show_when_values())
        copy.save(update_fields=['show_when_parent_values', 'show_when_parent_value'])
    _copy_options(original, copy)
    return copy


@transaction.atomic
def set_assignment(report_type, target, active, user, notes=None):
    """Assign a report type to a customer or a distributor, or withdraw it.

    ``target`` is a Customer or a Distributor. Withdrawing keeps the row with
    ``is_active`` off rather than deleting it, so its history stays. The
    person who switches it on is recorded as the assigner.
    """
    from chemsapp.models import Customer

    if isinstance(target, Customer):
        model, field = ReportTypeCustomer, 'customer'
    else:
        model, field = ReportTypeDistributor, 'distributor'

    assignment, created = model.objects.get_or_create(
        report_type=report_type, **{field: target},
        defaults={'assigned_by': user, 'is_active': active, 'notes': notes})
    if not created:
        assignment.is_active = active
        update = ['is_active']
        if active:
            assignment.assigned_by = user
            update.append('assigned_by')
        if notes is not None:
            assignment.notes = notes
            update.append('notes')
        assignment.save(update_fields=update)
    return assignment


class ReorderError(ValueError):
    """The posted order names a section or question outside this type."""


@transaction.atomic
def reorder(report_type, section_ids, questions_by_section):
    """Write the order the builder's drag-and-drop arrived at.

    ``section_ids`` lists the type's sections, top to bottom.
    ``questions_by_section`` maps a section id (or ``None`` for questions in
    no section) to its question ids, top to bottom. A question listed under
    a different section from the one it is in moves there.

    Every id must belong to this report type, so a stale screen cannot move
    another type's question into this one.
    """
    own_sections = set(report_type.sections.values_list('pk', flat=True))
    own_questions = set(report_type.questions.values_list('pk', flat=True))

    unknown_sections = set(section_ids) - own_sections
    if unknown_sections:
        raise ReorderError(f'Sections not in this report type: {sorted(unknown_sections)}')
    for section_id, question_ids in questions_by_section.items():
        if section_id is not None and section_id not in own_sections:
            raise ReorderError(f'Section {section_id} is not in this report type.')
        stray = set(question_ids) - own_questions
        if stray:
            raise ReorderError(f'Questions not in this report type: {sorted(stray)}')

    for position, section_id in enumerate(section_ids):
        ReportSection.objects.filter(pk=section_id).update(order=position)
    for section_id, question_ids in questions_by_section.items():
        for position, question_id in enumerate(question_ids):
            Question.objects.filter(pk=question_id).update(
                section_id=section_id, order=position)


def _file(field):
    if not field:
        return None
    try:
        return {'name': field.name.rsplit('/', 1)[-1], 'url': field.url}
    except ValueError:
        return None


def option_json(option):
    return {
        'id': option.pk,
        'text': option.text,
        'value': option.value,
        'is_flag': option.is_flag,
        'badge_type': option.badge_type,
        'additional_instructions': option.additional_instructions,
        'attached_pdf': _file(option.attached_pdf),
        'order': option.order,
    }


def question_json(question):
    return {
        'id': question.pk,
        'section_id': question.section_id,
        'question_text': question.question_text,
        'question_type': question.question_type,
        'help_text': question.help_text,
        'is_required': question.is_required,
        'order': question.order,
        'parent_question_id': question.parent_question_id,
        'show_when_parent_values': question.get_show_when_values(),
        'options': [option_json(option) for option in question.options.all()],
    }


def section_json(section):
    return {
        'id': section.pk,
        'name': section.name,
        'description': section.description,
        'order': section.order,
    }


def report_type_json(report_type):
    """The type's own fields, without its structure."""
    return {
        'id': report_type.pk,
        'name': report_type.name,
        'description': report_type.description,
        'category': report_type.category,
        'prefix': report_type.auto_number_prefix,
        'is_active': report_type.is_active,
    }


def builder_tree(report_type):
    """Everything the builder draws: the type, its sections, and its
    questions with their options, in the order the app user sees them.
    """
    sections = report_type.sections.order_by('order', 'name')
    questions = (
        report_type.questions
        .select_related('section')
        .prefetch_related('options')
        .order_by('section__order', 'order', 'question_text')
    )
    counts = report_type.reports.aggregate(total=Count('pk'))
    return {
        **report_type_json(report_type),
        'report_count': counts['total'],
        'sections': [section_json(section) for section in sections],
        'questions': [question_json(question) for question in questions],
    }
