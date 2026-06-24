import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from properties.models import Property
from units.models import Unit
from website.models import Inquiry
from tenants.models import Tenancy, MaintenanceRequest
from accounts.models import landlord_subscription_status, landlord_has_active_sub

@login_required
def overview(request):
    if request.user.profile.role != 'landlord':
        return render(request, 'dashboard/overview.html', {'access_denied': True})
    if not landlord_has_active_sub(request.user):
        sub_status, _ = landlord_subscription_status(request.user)
        return render(request, 'dashboard/locked.html', {'sub_status': sub_status, 'active_tab': 'overview'})

    properties = request.user.properties.annotate(
        unit_count=Count('units'),
        vacant_count=Count('units', filter=Q(units__status='vacant')),
    )
    total_units = Unit.objects.filter(property__owner=request.user).count()
    vacant_units = Unit.objects.filter(property__owner=request.user, status='vacant').count()
    occupied_units = Unit.objects.filter(property__owner=request.user, status='occupied').count()
    occupancy_rate = round((occupied_units / total_units * 100)) if total_units else 0
    unread_inquiries = Inquiry.objects.filter(unit__property__owner=request.user, is_read=False).count()
    recent_inquiries = Inquiry.objects.filter(unit__property__owner=request.user).order_by('-created_at')[:5]
    active_tenancies = Tenancy.objects.filter(unit__property__owner=request.user, status='active').count()
    urgent_maintenance = MaintenanceRequest.objects.filter(unit__property__owner=request.user, priority='urgent', status__in=['submitted', 'in_progress']).count()

    # Recent activity log
    recent_activity = []
    for u in Unit.objects.filter(property__owner=request.user).order_by('-created_at')[:3]:
        recent_activity.append({'type': 'unit', 'text': f'Unit {u.unit_number} added at {u.property.name}', 'time': u.created_at})
    for t in Tenancy.objects.filter(unit__property__owner=request.user).order_by('-created_at')[:3]:
        recent_activity.append({'type': 'tenant', 'text': f'{t.tenant.username} assigned to {t.unit.unit_number}', 'time': t.created_at})
    for i in Inquiry.objects.filter(unit__property__owner=request.user).order_by('-created_at')[:3]:
        recent_activity.append({'type': 'inquiry', 'text': f'Inquiry from {i.name} about {i.unit.unit_number}', 'time': i.created_at})
    recent_activity.sort(key=lambda x: x['time'], reverse=True)
    recent_activity = recent_activity[:8]

    # Chart: property occupancy breakdown
    chart_prop_labels = []
    chart_prop_vacant = []
    chart_prop_occupied = []
    for p in properties:
        chart_prop_labels.append(p.name[:12])
        chart_prop_vacant.append(p.vacant_count)
        chart_prop_occupied.append(p.unit_count - p.vacant_count)

    # Chart: unit type distribution
    type_data = Unit.objects.filter(property__owner=request.user).values('house_type').annotate(count=Count('id')).order_by('-count')
    type_labels = []
    type_counts = []
    type_colors = ['#8b5cf6', '#3b82f6', '#34d399', '#f59e0b', '#f87171', '#60a5fa']
    for t in type_data:
        type_labels.append(dict(Unit.HOUSE_TYPES).get(t['house_type'], t['house_type']))
        type_counts.append(t['count'])

    # Chart: inquiries over last 7 days
    today = timezone.now().date()
    inquiry_dates = []
    inquiry_counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        inquiry_dates.append(day.strftime('%a'))
        inquiry_counts.append(Inquiry.objects.filter(unit__property__owner=request.user, created_at__date=day).count())

    sub_status, sub = landlord_subscription_status(request.user)
    ctx = {
        'active_tab': 'overview',
        'properties_count': properties.count(),
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'occupancy_rate': occupancy_rate,
        'unread_inquiries': unread_inquiries,
        'recent_inquiries': recent_inquiries,
        'active_tenancies': active_tenancies,
        'urgent_maintenance': urgent_maintenance,
        'recent_activity': recent_activity,
        'properties': properties,
        'chart_prop_labels': json.dumps(chart_prop_labels),
        'chart_prop_vacant': json.dumps(chart_prop_vacant),
        'chart_prop_occupied': json.dumps(chart_prop_occupied),
        'type_labels': json.dumps(type_labels),
        'type_counts': json.dumps(type_counts),
        'type_colors': json.dumps(type_colors[:len(type_labels)]),
        'inquiry_dates': json.dumps(inquiry_dates),
        'inquiry_counts': json.dumps(inquiry_counts),
        'sub_status': sub_status,
        'sub': sub,
    }
    return render(request, 'dashboard/overview.html', ctx)


@login_required
def inquiries(request):
    if request.user.profile.role != 'landlord':
        return render(request, 'dashboard/overview.html', {'access_denied': True})
    if not landlord_has_active_sub(request.user):
        return render(request, 'dashboard/locked.html', {'active_tab': 'inquiries'})
    qs = Inquiry.objects.filter(unit__property__owner=request.user).select_related('unit', 'unit__property').order_by('-created_at')
    if request.GET.get('mark_read'):
        Inquiry.objects.filter(pk=request.GET['mark_read'], unit__property__owner=request.user).update(is_read=True)
        return redirect('dashboard:inquiries')
    return render(request, 'dashboard/inquiries.html', {'inquiries': qs, 'active_tab': 'inquiries'})
