from django import template
from tenants.models import RentPayment
from django.db.models import Sum

register = template.Library()

@register.filter
def dict_get(d, key):
    return d.get(key)

@register.inclusion_tag('tenants/_rent_reminder.html', takes_context=True)
def rent_reminder(context):
    user = context['request'].user
    if user.is_anonymous or user.profile.role != 'tenant':
        return {'show': False}
    qs = RentPayment.objects.filter(tenancy__tenant=user, status__in=['pending', 'overdue']).exclude(notes='stk_intermediary')
    overdue = qs.filter(status='overdue').count()
    pending = qs.filter(status='pending').count()
    total = qs.aggregate(s=Sum('amount'))['s'] or 0
    if overdue == 0 and pending == 0:
        return {'show': False}
    return {'show': True, 'overdue_count': overdue, 'pending_count': pending, 'total_balance': total}
