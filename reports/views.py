from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from .models import (
    ReportType, ReportSection, Question, QuestionOption, 
    Report, Answer, QUESTION_TYPES
)
from .forms import (
    ReportTypeForm, ReportSectionForm, QuestionForm, 
    QuestionOptionForm, ReportForm
)
from chemsapp.models import Customer, Distributor


@login_required
def report_type_list(request):
    """List all report types"""
    report_types = ReportType.objects.filter(is_active=True).order_by('-created_at')
    paginator = Paginator(report_types, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Report Types'
    }
    return render(request, 'reports/report_type_list.html', context)


@login_required
def report_type_create(request):
    """Create a new report type"""
    if request.method == 'POST':
        form = ReportTypeForm(request.POST)
        if form.is_valid():
            report_type = form.save(commit=False)
            report_type.created_by = request.user
            report_type.save()
            messages.success(request, f'Report type "{report_type.name}" created successfully!')
            return redirect('reports:report_type_detail', pk=report_type.pk)
    else:
        form = ReportTypeForm()
    
    context = {
        'form': form,
        'title': 'Create Report Type'
    }
    return render(request, 'reports/report_type_form.html', context)


@login_required
def report_type_detail(request, pk):
    """View report type details with sections and questions"""
    report_type = get_object_or_404(ReportType, pk=pk)
    sections = report_type.sections.all().order_by('order')
    questions = report_type.questions.all().order_by('section__order', 'order')
    
    context = {
        'report_type': report_type,
        'sections': sections,
        'questions': questions,
        'title': f'Report Type: {report_type.name}'
    }
    return render(request, 'reports/report_type_detail.html', context)


@login_required
def report_type_edit(request, pk):
    """Edit an existing report type"""
    report_type = get_object_or_404(ReportType, pk=pk)
    
    if request.method == 'POST':
        form = ReportTypeForm(request.POST, instance=report_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Report type "{report_type.name}" updated successfully!')
            return redirect('reports:report_type_detail', pk=report_type.pk)
    else:
        form = ReportTypeForm(instance=report_type)
    
    context = {
        'form': form,
        'report_type': report_type,
        'title': f'Edit: {report_type.name}'
    }
    return render(request, 'reports/report_type_form.html', context)


@login_required
def report_type_delete(request, pk):
    """Delete a report type"""
    report_type = get_object_or_404(ReportType, pk=pk)
    
    if request.method == 'POST':
        name = report_type.name
        report_type.delete()
        messages.success(request, f'Report type "{name}" deleted successfully!')
        return redirect('reports:report_type_list')
    
    context = {
        'report_type': report_type,
        'title': f'Delete: {report_type.name}'
    }
    return render(request, 'reports/report_type_confirm_delete.html', context)


@login_required
def report_type_duplicate(request, pk):
    """Duplicate an existing report type with all its structure"""
    original_report_type = get_object_or_404(ReportType, pk=pk)
    
    if request.method == 'POST':
        form = ReportTypeForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create new report type
                    new_report_type = form.save(commit=False)
                    new_report_type.created_by = request.user
                    new_report_type.save()
                    
                    # Create mapping of old section IDs to new sections
                    section_mapping = {}
                    
                    # Duplicate sections
                    for old_section in original_report_type.sections.all():
                        new_section = ReportSection.objects.create(
                            report_type=new_report_type,
                            name=old_section.name,
                            description=old_section.description,
                            order=old_section.order
                        )
                        section_mapping[old_section.id] = new_section
                    
                    # Create mapping of old question IDs to new questions
                    question_mapping = {}
                    
                    # Duplicate questions (first pass - without parent relationships)
                    for old_question in original_report_type.questions.all():
                        new_question = Question.objects.create(
                            report_type=new_report_type,
                            section=section_mapping.get(old_question.section_id) if old_question.section_id else None,
                            question_text=old_question.question_text,
                            question_type=old_question.question_type,
                            help_text=old_question.help_text,
                            is_required=old_question.is_required,
                            order=old_question.order
                        )
                        question_mapping[old_question.id] = new_question
                    
                    # Second pass - establish parent-child relationships and conditional logic
                    for old_question in original_report_type.questions.all():
                        new_question = question_mapping[old_question.id]
                        if old_question.parent_question_id:
                            new_question.parent_question = question_mapping.get(old_question.parent_question_id)
                        
                        # Copy conditional values
                        trigger_values = old_question.get_show_when_values()
                        if trigger_values:
                            new_question.set_show_when_values(trigger_values)
                        
                        new_question.save()
                    
                    # Duplicate question options
                    for old_question in original_report_type.questions.all():
                        new_question = question_mapping[old_question.id]
                        for old_option in old_question.options.all():
                            QuestionOption.objects.create(
                                question=new_question,
                                text=old_option.text,
                                value=old_option.value,
                                is_flag=old_option.is_flag,
                                additional_instructions=old_option.additional_instructions,
                                order=old_option.order
                                # Note: attached_pdf is not copied to avoid file duplication issues
                            )
                    
                    messages.success(
                        request, 
                        f'Report type "{new_report_type.name}" created successfully as a copy of "{original_report_type.name}"! '
                        f'Copied {len(section_mapping)} sections, {len(question_mapping)} questions, and their options.'
                    )
                    return redirect('reports:report_type_detail', pk=new_report_type.pk)
                    
            except Exception as e:
                messages.error(request, f'Error duplicating report type: {str(e)}')
                
    else:
        # Pre-populate form with original data but change the name
        initial_data = {
            'name': f"{original_report_type.name} (Copy)",
            'description': original_report_type.description,
            'auto_number_prefix': f"{original_report_type.auto_number_prefix}C" if original_report_type.auto_number_prefix else None,
            'is_active': original_report_type.is_active
        }
        form = ReportTypeForm(initial=initial_data)
    
    context = {
        'form': form,
        'original_report_type': original_report_type,
        'title': f'Duplicate: {original_report_type.name}'
    }
    return render(request, 'reports/report_type_duplicate.html', context)


@login_required
def section_create(request, report_type_id):
    """Create a new section"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    
    if request.method == 'POST':
        form = ReportSectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.report_type = report_type
            section.save()
            messages.success(request, f'Section "{section.name}" created successfully!')
            return redirect('reports:report_type_detail', pk=report_type.pk)
    else:
        form = ReportSectionForm()
    
    context = {
        'form': form,
        'report_type': report_type,
        'title': f'Create Section for {report_type.name}'
    }
    return render(request, 'reports/section_form.html', context)


@login_required
def section_edit(request, pk):
    """Edit a section"""
    section = get_object_or_404(ReportSection, pk=pk)
    
    if request.method == 'POST':
        form = ReportSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, f'Section "{section.name}" updated successfully!')
            return redirect('reports:report_type_detail', pk=section.report_type.pk)
    else:
        form = ReportSectionForm(instance=section)
    
    context = {
        'form': form,
        'section': section,
        'report_type': section.report_type,
        'title': f'Edit Section: {section.name}'
    }
    return render(request, 'reports/section_form.html', context)


@login_required
def section_delete(request, pk):
    """Delete a section"""
    section = get_object_or_404(ReportSection, pk=pk)
    report_type = section.report_type
    
    if request.method == 'POST':
        name = section.name
        section.delete()
        messages.success(request, f'Section "{name}" deleted successfully!')
        return redirect('reports:report_type_detail', pk=report_type.pk)
    
    context = {
        'section': section,
        'title': f'Delete Section: {section.name}'
    }
    return render(request, 'reports/section_confirm_delete.html', context)


@login_required
def section_duplicate(request, pk):
    """Duplicate a section with all its questions"""
    original_section = get_object_or_404(ReportSection, pk=pk)
    report_type = original_section.report_type
    
    if request.method == 'POST':
        form = ReportSectionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create new section
                    new_section = form.save(commit=False)
                    new_section.report_type = report_type
                    new_section.save()
                    
                    # Get all questions in the original section
                    original_questions = original_section.questions.all()
                    
                    # Create mapping for question relationships
                    question_mapping = {}
                    
                    # First pass: Duplicate questions without parent relationships
                    for old_question in original_questions:
                        new_question = Question.objects.create(
                            report_type=report_type,
                            section=new_section,
                            question_text=old_question.question_text,
                            question_type=old_question.question_type,
                            help_text=old_question.help_text,
                            is_required=old_question.is_required,
                            order=old_question.order
                        )
                        question_mapping[old_question.id] = new_question
                    
                    # Second pass: Establish parent-child relationships within duplicated questions
                    for old_question in original_questions:
                        new_question = question_mapping[old_question.id]
                        if old_question.parent_question_id and old_question.parent_question_id in question_mapping:
                            # Only set parent if the parent is also in this section
                            new_question.parent_question = question_mapping[old_question.parent_question_id]
                            
                            # Copy conditional values
                            trigger_values = old_question.get_show_when_values()
                            if trigger_values:
                                new_question.set_show_when_values(trigger_values)
                            
                            new_question.save()
                    
                    # Duplicate question options
                    for old_question in original_questions:
                        new_question = question_mapping[old_question.id]
                        for old_option in old_question.options.all():
                            QuestionOption.objects.create(
                                question=new_question,
                                text=old_option.text,
                                value=old_option.value,
                                is_flag=old_option.is_flag,
                                additional_instructions=old_option.additional_instructions,
                                order=old_option.order
                            )
                    
                    messages.success(
                        request, 
                        f'Section "{new_section.name}" created successfully as a copy of "{original_section.name}"! '
                        f'Copied {len(question_mapping)} questions and their options.'
                    )
                    return redirect('reports:report_type_detail', pk=report_type.pk)
                    
            except Exception as e:
                messages.error(request, f'Error duplicating section: {str(e)}')
    
    else:
        # Pre-populate form with original data but change the name
        initial_data = {
            'name': f"{original_section.name} (Copy)",
            'description': original_section.description,
            'order': original_section.order + 1  # Place it after the original
        }
        form = ReportSectionForm(initial=initial_data)
    
    context = {
        'form': form,
        'original_section': original_section,
        'report_type': report_type,
        'title': f'Duplicate Section: {original_section.name}'
    }
    return render(request, 'reports/section_duplicate.html', context)


@login_required
def question_create(request, report_type_id):
    """Create a new question"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, report_type=report_type)
        if form.is_valid():
            question = form.save(commit=False)
            question.report_type = report_type
            question.save()
            messages.success(request, f'Question created successfully!')
            
            # If it's a choice question, redirect to add options
            if question.question_type in ['select', 'radio', 'checkbox']:
                return redirect('reports:question_options', pk=question.pk)
            else:
                return redirect('reports:report_type_detail', pk=report_type.pk)
    else:
        form = QuestionForm(report_type=report_type)
    
    context = {
        'form': form,
        'report_type': report_type,
        'question_types': QUESTION_TYPES,
        'title': f'Create Question for {report_type.name}'
    }
    return render(request, 'reports/question_form.html', context)


@login_required
def question_edit(request, pk):
    """Edit a question"""
    question = get_object_or_404(Question, pk=pk)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question, report_type=question.report_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Question updated successfully!')
            return redirect('reports:report_type_detail', pk=question.report_type.pk)
    else:
        form = QuestionForm(instance=question, report_type=question.report_type)
    
    context = {
        'form': form,
        'question': question,
        'report_type': question.report_type,
        'question_types': QUESTION_TYPES,
        'title': f'Edit Question'
    }
    return render(request, 'reports/question_form.html', context)


@login_required
def question_delete(request, pk):
    """Delete a question"""
    question = get_object_or_404(Question, pk=pk)
    report_type = question.report_type
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, f'Question deleted successfully!')
        return redirect('reports:report_type_detail', pk=report_type.pk)
    
    context = {
        'question': question,
        'title': f'Delete Question'
    }
    return render(request, 'reports/question_confirm_delete.html', context)


@login_required
def question_options(request, pk):
    """Manage options for a question"""
    question = get_object_or_404(Question, pk=pk)
    options = question.options.all().order_by('order')
    
    context = {
        'question': question,
        'options': options,
        'title': f'Options for: {question.question_text[:50]}...'
    }
    return render(request, 'reports/question_options.html', context)


@login_required
def option_create(request, question_id):
    """Create a new option for a question"""
    question = get_object_or_404(Question, pk=question_id)
    
    if request.method == 'POST':
        form = QuestionOptionForm(request.POST, request.FILES)
        if form.is_valid():
            option = form.save(commit=False)
            option.question = question
            option.save()
            messages.success(request, f'Option "{option.text}" created successfully!')
            return redirect('reports:question_options', pk=question.pk)
    else:
        form = QuestionOptionForm()
    
    context = {
        'form': form,
        'question': question,
        'title': f'Create Option for Question'
    }
    return render(request, 'reports/option_form.html', context)


@login_required
def option_edit(request, pk):
    """Edit an option"""
    option = get_object_or_404(QuestionOption, pk=pk)
    
    if request.method == 'POST':
        form = QuestionOptionForm(request.POST, request.FILES, instance=option)
        if form.is_valid():
            form.save()
            messages.success(request, f'Option "{option.text}" updated successfully!')
            return redirect('reports:question_options', pk=option.question.pk)
    else:
        form = QuestionOptionForm(instance=option)
    
    context = {
        'form': form,
        'option': option,
        'title': f'Edit Option: {option.text}'
    }
    return render(request, 'reports/option_form.html', context)


@login_required
def option_delete(request, pk):
    """Delete an option"""
    option = get_object_or_404(QuestionOption, pk=pk)
    question = option.question
    
    if request.method == 'POST':
        text = option.text
        option.delete()
        messages.success(request, f'Option "{text}" deleted successfully!')
        return redirect('reports:question_options', pk=question.pk)
    
    context = {
        'option': option,
        'title': f'Delete Option: {option.text}'
    }
    return render(request, 'reports/option_confirm_delete.html', context)


@login_required
def report_list(request):
    """List all report instances"""
    reports = Report.objects.all().order_by('-created_at')
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Reports'
    }
    return render(request, 'reports/report_list.html', context)


@login_required
def report_create(request, report_type_id):
    """Create a new report instance"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    
    if request.method == 'POST':
        form = ReportForm(request.POST, report_type=report_type)
        if form.is_valid():
            report = form.save(commit=False)
            report.report_type = report_type
            report.prepared_by = request.user
            report.save()
            messages.success(request, f'Report "{report.document_number}" created successfully!')
            return redirect('reports:report_fill', pk=report.pk)
    else:
        form = ReportForm(report_type=report_type)
    
    context = {
        'form': form,
        'report_type': report_type,
        'title': f'Create New {report_type.name}'
    }
    return render(request, 'reports/report_create.html', context)


@login_required
def report_detail(request, pk):
    """View report details and answers"""
    report = get_object_or_404(Report, pk=pk)
    answers = report.answers.all().select_related('question')
    
    context = {
        'report': report,
        'answers': answers,
        'title': f'Report: {report.document_number}'
    }
    return render(request, 'reports/report_detail.html', context)


@login_required
def report_fill(request, pk):
    """Fill out a report with answers"""
    report = get_object_or_404(Report, pk=pk)
    questions = report.report_type.questions.all().order_by('section__order', 'order')
    
    if request.method == 'POST':
        with transaction.atomic():
            for question in questions:
                answer, created = Answer.objects.get_or_create(
                    report=report,
                    question=question
                )
                
                # Handle different question types
                if question.question_type in ['text', 'textarea']:
                    answer.text_answer = request.POST.get(f'question_{question.id}', '')
                elif question.question_type == 'number':
                    try:
                        value = request.POST.get(f'question_{question.id}', '')
                        answer.number_answer = float(value) if value else None
                    except ValueError:
                        answer.number_answer = None
                elif question.question_type == 'date':
                    from django.utils.dateparse import parse_date
                    date_str = request.POST.get(f'question_{question.id}', '')
                    answer.date_answer = parse_date(date_str) if date_str else None
                elif question.question_type in ['select', 'radio']:
                    option_value = request.POST.get(f'question_{question.id}')
                    if option_value:
                        answer.selected_options.clear()
                        try:
                            option = QuestionOption.objects.get(question=question, value=option_value)
                            answer.selected_options.add(option)
                        except QuestionOption.DoesNotExist:
                            pass
                elif question.question_type == 'checkbox':
                    option_values = request.POST.getlist(f'question_{question.id}')
                    answer.selected_options.clear()
                    for option_value in option_values:
                        try:
                            option = QuestionOption.objects.get(question=question, value=option_value)
                            answer.selected_options.add(option)
                        except QuestionOption.DoesNotExist:
                            pass
                elif question.question_type == 'yesno':
                    value = request.POST.get(f'question_{question.id}')
                    answer.text_answer = value if value in ['yes', 'no'] else ''
                
                answer.save()
        
        messages.success(request, 'Report answers saved successfully!')
        return redirect('reports:report_detail', pk=report.pk)
    
    # Get existing answers
    existing_answers = {
        answer.question.id: answer 
        for answer in report.answers.all()
    }
    
    context = {
        'report': report,
        'questions': questions,
        'existing_answers': existing_answers,
        'title': f'Fill Report: {report.document_number}'
    }
    return render(request, 'reports/report_fill.html', context)


@login_required
def report_submit(request, pk):
    """Submit a report for review"""
    report = get_object_or_404(Report, pk=pk)
    
    if request.method == 'POST':
        report.status = 'submitted'
        from django.utils import timezone
        report.submitted_at = timezone.now()
        report.save()
        messages.success(request, f'Report "{report.document_number}" submitted for review!')
        return redirect('reports:report_detail', pk=report.pk)
    
    context = {
        'report': report,
        'title': f'Submit Report: {report.document_number}'
    }
    return render(request, 'reports/report_submit.html', context)


@login_required
def create_sample_grocery_report(request):
    """Create a sample grocery store audit report based on the CSV"""
    if request.method == 'POST':
        from django.core.management import call_command
        from io import StringIO
        
        try:
            # Capture the command output
            out = StringIO()
            call_command('create_sample_grocery_report', stdout=out)
            
            # Check if report was created
            report_type = ReportType.objects.filter(name="Monthly Audit Report - Grocery").first()
            if report_type:
                messages.success(request, f'Sample grocery store report template created successfully! {report_type.questions.count()} questions added.')
                return redirect('reports:report_type_detail', pk=report_type.pk)
            else:
                messages.error(request, 'Failed to create sample report template.')
        except Exception as e:
            messages.error(request, f'Error creating sample report: {str(e)}')
        
        return redirect('reports:report_type_list')
    
    # Check if sample already exists
    existing_sample = ReportType.objects.filter(name="Monthly Audit Report - Grocery").first()
    
    context = {
        'title': 'Create Sample Grocery Store Report',
        'existing_sample': existing_sample
    }
    return render(request, 'reports/create_sample.html', context)


@login_required
def get_question_options_ajax(request, question_id):
    """AJAX endpoint to get options for a question"""
    try:
        question = get_object_or_404(Question, pk=question_id)
        
        if question.question_type == 'yesno':
            options = [
                {'value': 'yes', 'text': 'Yes'},
                {'value': 'no', 'text': 'No'}
            ]
        elif question.question_type in ['select', 'radio', 'checkbox']:
            options = [
                {'value': option.value, 'text': option.text}
                for option in question.options.all().order_by('order')
            ]
        else:
            options = []
        
        return JsonResponse({
            'success': True,
            'options': options,
            'question_type': question.question_type,
            'question_text': question.question_text
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
