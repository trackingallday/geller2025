from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db import transaction
from django.forms.models import model_to_dict
import json

from .models import (
    ReportType, ReportSection, Question, QuestionOption, QuestionTemplate,
    ReportTypeCustomer, ConditionalRule, QUESTION_TYPES
)
from .forms import ReportTypeForm
from chemsapp.models import Customer


@login_required
def report_builder_wizard(request):
    """Multi-step wizard for creating enhanced report types"""
    step = request.GET.get('step', '1')
    report_type_id = request.GET.get('report_type_id')
    
    if report_type_id:
        report_type = get_object_or_404(ReportType, pk=report_type_id)
    else:
        report_type = None
    
    context = {
        'step': step,
        'report_type': report_type,
        'title': 'Create Report Type - Step ' + step
    }
    
    if step == '1':
        # Step 1: Basic report type info
        if request.method == 'POST':
            form = ReportTypeForm(request.POST, instance=report_type)
            if form.is_valid():
                report_type = form.save(commit=False)
                if not report_type.pk:
                    report_type.created_by = request.user
                report_type.save()
                messages.success(request, f'Report type "{report_type.name}" saved!')
                return redirect(f'/reports/builder/wizard/?step=2&report_type_id={report_type.pk}')
        else:
            form = ReportTypeForm(instance=report_type)
        
        context.update({
            'form': form,
            'next_step': '2'
        })
        
    elif step == '2':
        # Step 2: Customer assignment
        if not report_type:
            messages.error(request, 'Please complete step 1 first.')
            return redirect('/reports/builder/wizard/?step=1')
        
        customers = Customer.objects.all()
        assigned_customers = report_type.get_assigned_customers()
        
        if request.method == 'POST':
            selected_customers = request.POST.getlist('customers')
            
            with transaction.atomic():
                # Deactivate all existing assignments
                ReportTypeCustomer.objects.filter(report_type=report_type).update(is_active=False)
                
                # Create/activate new assignments
                for customer_id in selected_customers:
                    try:
                        customer = Customer.objects.get(pk=customer_id)
                        report_type.assign_to_customer(customer, assigned_by=request.user)
                    except Customer.DoesNotExist:
                        continue
            
            messages.success(request, 'Customer assignments updated!')
            return redirect(f'/reports/builder/{report_type.pk}/')
        
        context.update({
            'customers': customers,
            'assigned_customers': assigned_customers,
            'next_step': 'builder'
        })
        
    return render(request, 'reports/builder/wizard.html', context)


@login_required 
def form_builder(request, report_type_id):
    """Main form builder interface with drag-and-drop functionality"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    sections = report_type.sections.all().order_by('order')
    questions = report_type.questions.all().order_by('section__order', 'order')
    templates = QuestionTemplate.objects.all().order_by('category', 'name')
    conditional_rules = report_type.conditional_rules.filter(is_active=True).order_by('order')
    
    context = {
        'report_type': report_type,
        'sections': sections,
        'questions': questions,
        'templates': templates,
        'conditional_rules': conditional_rules,
        'question_types': QUESTION_TYPES,
        'assigned_customers': report_type.get_assigned_customers(),
        'title': f'Form Builder - {report_type.name}'
    }
    
    return render(request, 'reports/builder/form_builder.html', context)


@login_required
@require_POST
def ajax_create_section(request, report_type_id):
    """AJAX endpoint to create a new section"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    
    try:
        data = json.loads(request.body)
        section = ReportSection.objects.create(
            report_type=report_type,
            name=data.get('name', 'New Section'),
            description=data.get('description', ''),
            order=data.get('order', 0)
        )
        
        return JsonResponse({
            'success': True,
            'section': {
                'id': section.id,
                'name': section.name,
                'description': section.description,
                'order': section.order
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def ajax_create_question(request, report_type_id):
    """AJAX endpoint to create a new question"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    
    try:
        data = json.loads(request.body)
        
        # Get section if provided
        section = None
        if data.get('section_id'):
            section = ReportSection.objects.get(pk=data['section_id'], report_type=report_type)
        
        question = Question.objects.create(
            report_type=report_type,
            section=section,
            question_text=data.get('question_text', 'New Question'),
            question_type=data.get('question_type', 'text'),
            help_text=data.get('help_text', ''),
            is_required=data.get('is_required', False),
            order=data.get('order', 0)
        )
        
        # Add options if it's a choice question
        if question.question_type in ['select', 'radio', 'checkbox'] and data.get('options'):
            for i, option_text in enumerate(data['options']):
                QuestionOption.objects.create(
                    question=question,
                    text=option_text,
                    value=option_text.lower().replace(' ', '_'),
                    badge_type='default',
                    order=i
                )
        
        return JsonResponse({
            'success': True,
            'question': {
                'id': question.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'question_type_display': question.get_question_type_display(),
                'is_required': question.is_required,
                'order': question.order,
                'section_id': section.id if section else None
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def ajax_create_from_template(request, report_type_id):
    """AJAX endpoint to create question from template"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    
    try:
        data = json.loads(request.body)
        template = get_object_or_404(QuestionTemplate, pk=data['template_id'])
        
        # Get section if provided
        section = None
        if data.get('section_id'):
            section = ReportSection.objects.get(pk=data['section_id'], report_type=report_type)
        
        question = Question.objects.create(
            report_type=report_type,
            section=section,
            question_text=template.question_text,
            question_type=template.question_type,
            help_text=template.help_text,
            is_required=template.is_required_default,
            order=data.get('order', 0)
        )
        
        # Add template options if available
        if template.template_options and question.question_type in ['select', 'radio', 'checkbox']:
            for i, option_data in enumerate(template.template_options):
                if isinstance(option_data, str):
                    option_text = option_data
                    option_value = option_data.lower().replace(' ', '_')
                    is_flag = False
                    badge_type = 'default'
                else:
                    option_text = option_data.get('text', '')
                    option_value = option_data.get('value', option_text.lower().replace(' ', '_'))
                    is_flag = option_data.get('is_flag', False)
                    badge_type = option_data.get('badge_type', 'default')

                QuestionOption.objects.create(
                    question=question,
                    text=option_text,
                    value=option_value,
                    is_flag=is_flag,
                    badge_type=badge_type,
                    order=i
                )
        
        # Increment template usage
        template.increment_usage()
        
        return JsonResponse({
            'success': True,
            'question': {
                'id': question.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'question_type_display': question.get_question_type_display(),
                'is_required': question.is_required,
                'order': question.order,
                'section_id': section.id if section else None
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def ajax_update_order(request, report_type_id):
    """AJAX endpoint to update question/section order"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    
    try:
        data = json.loads(request.body)
        item_type = data.get('type')  # 'question' or 'section'
        items = data.get('items', [])
        
        if item_type == 'question':
            for item in items:
                Question.objects.filter(
                    pk=item['id'], 
                    report_type=report_type
                ).update(order=item['order'])
        elif item_type == 'section':
            for item in items:
                ReportSection.objects.filter(
                    pk=item['id'], 
                    report_type=report_type
                ).update(order=item['order'])
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def ajax_delete_item(request, report_type_id):
    """AJAX endpoint to delete question or section"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    
    try:
        data = json.loads(request.body)
        item_type = data.get('type')
        item_id = data.get('id')
        
        if item_type == 'question':
            Question.objects.filter(pk=item_id, report_type=report_type).delete()
        elif item_type == 'section':
            ReportSection.objects.filter(pk=item_id, report_type=report_type).delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def customer_assignments(request, report_type_id):
    """Manage customer assignments for a report type"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    customers = Customer.objects.all()
    assignments = ReportTypeCustomer.objects.filter(
        report_type=report_type
    ).select_related('customer', 'assigned_by').order_by('customer__businessName')
    
    if request.method == 'POST':
        selected_customers = request.POST.getlist('customers')
        notes = request.POST.get('notes', '')
        
        with transaction.atomic():
            # Deactivate all existing assignments
            ReportTypeCustomer.objects.filter(report_type=report_type).update(is_active=False)
            
            # Create/activate new assignments
            for customer_id in selected_customers:
                try:
                    customer = Customer.objects.get(pk=customer_id)
                    assignment = report_type.assign_to_customer(
                        customer, 
                        assigned_by=request.user,
                        notes=notes
                    )
                except Customer.DoesNotExist:
                    continue
        
        messages.success(request, f'Customer assignments updated for "{report_type.name}"')
        return redirect('reports:form_builder', report_type_id=report_type.pk)
    
    context = {
        'report_type': report_type,
        'customers': customers,
        'assignments': assignments,
        'assigned_customers': report_type.get_assigned_customers(),
        'title': f'Customer Assignments - {report_type.name}'
    }
    
    return render(request, 'reports/builder/customer_assignments.html', context)


@login_required
def question_templates(request):
    """Manage question templates"""
    templates = QuestionTemplate.objects.all().order_by('category', 'usage_count')
    paginator = Paginator(templates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'templates': templates,
        'title': 'Question Templates'
    }
    
    return render(request, 'reports/builder/question_templates.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def conditional_rules(request, report_type_id):
    """Manage conditional rules for a report type"""
    report_type = get_object_or_404(ReportType, pk=report_type_id)
    rules = report_type.conditional_rules.all().order_by('order')
    questions = report_type.questions.all().order_by('section__order', 'order')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            rule = ConditionalRule.objects.create(
                name=data.get('name'),
                report_type=report_type,
                trigger_question_id=data.get('trigger_question'),
                trigger_value=data.get('trigger_value'),
                trigger_operator=data.get('trigger_operator', 'equals'),
                target_question_id=data.get('target_question'),
                action=data.get('action'),
                order=data.get('order', rules.count())
            )
            
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'rule': {
                        'id': rule.id,
                        'name': rule.name,
                        'trigger_question': rule.trigger_question.question_text[:50],
                        'trigger_value': rule.trigger_value,
                        'action': rule.get_action_display(),
                        'target_question': rule.target_question.question_text[:50]
                    }
                })
            else:
                messages.success(request, f'Conditional rule "{rule.name}" created successfully!')
                return redirect('reports:conditional_rules', report_type_id=report_type.pk)
                
        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error creating rule: {str(e)}')
    
    context = {
        'report_type': report_type,
        'rules': rules,
        'questions': questions,
        'title': f'Conditional Rules - {report_type.name}'
    }
    
    return render(request, 'reports/builder/conditional_rules.html', context)