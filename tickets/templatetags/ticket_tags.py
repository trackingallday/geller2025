from django import template

register = template.Library()

STATUS_COLORS = {
    'pending': 'warning',
    'read': 'info',
    'completed': 'success',
    'cancelled': 'secondary',
}


@register.filter
def status_color(value):
    return STATUS_COLORS.get(value, 'secondary')
