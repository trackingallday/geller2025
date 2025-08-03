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
                    option_id = request.POST.get(f'question_{question.id}')
                    if option_id:
                        answer.selected_options.clear()
                        try:
                            option = QuestionOption.objects.get(id=option_id)
                            answer.selected_options.add(option)
                        except QuestionOption.DoesNotExist:
                            pass
                elif question.question_type == 'checkbox':
                    option_ids = request.POST.getlist(f'question_{question.id}')
                    answer.selected_options.clear()
                    for option_id in option_ids:
                        try:
                            option = QuestionOption.objects.get(id=option_id)
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
