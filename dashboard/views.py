import json
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from properties.models import Property
from units.models import Unit
from website.models import Inquiry
from tenants.models import Tenancy, MaintenanceRequest, RentPayment, LeaseAgreement
from accounts.models import landlord_subscription_status, landlord_has_active_sub, get_fee_per_unit, landlord_trial_info
from core.pagination import paginate

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
        occupied_count=Count('units', filter=Q(units__status='occupied')),
    )
    total_units = Unit.objects.filter(property__owner=request.user).count()
    vacant_units = Unit.objects.filter(property__owner=request.user, status='vacant').count()
    occupied_units = Unit.objects.filter(property__owner=request.user, status='occupied').count()
    occupancy_rate = round((occupied_units / total_units * 100)) if total_units else 0
    active_tenancies = Tenancy.objects.filter(unit__property__owner=request.user, status='active').count()
    unread_inquiries = Inquiry.objects.filter(unit__property__owner=request.user, is_read=False).count()
    urgent_maintenance_count = MaintenanceRequest.objects.filter(unit__property__owner=request.user, priority='urgent', status__in=['submitted', 'in_progress']).count()

    # Rent collection stats
    all_payments = RentPayment.objects.filter(tenancy__unit__property__owner=request.user)
    total_collected = all_payments.filter(status='paid').aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    pending_total = all_payments.filter(status='pending').aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    overdue_total = all_payments.filter(status='overdue').aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    pending_count = all_payments.filter(status='pending').count()
    overdue_count = all_payments.filter(status='overdue').count()
    collection_rate = round((total_collected / (total_collected + pending_total + overdue_total) * 100)) if (total_collected + pending_total + overdue_total) else 0

    # Monthly collection (current month)
    today = timezone.now().date()
    month_start = today.replace(day=1)
    monthly_collected = all_payments.filter(status='paid', paid_date__gte=month_start).aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    monthly_expected = all_payments.filter(due_date__gte=month_start, due_date__lte=month_start + timedelta(days=31)).aggregate(s=Sum('amount'))['s'] or Decimal('0.00')

    # Leases expiring soon (within 30 days)
    today = timezone.now().date()
    expiring_leases = LeaseAgreement.objects.filter(
        tenancy__unit__property__owner=request.user,
        status='active',
        end_date__gte=today,
        end_date__lte=today + timedelta(days=30),
    ).select_related('tenancy__tenant', 'tenancy__unit')

    # Subscription info
    sub_status, sub = landlord_subscription_status(request.user)
    fee_per_unit = get_fee_per_unit(request.user)
    trial_info = landlord_trial_info(request.user)
    monthly_sub_fee = total_units * fee_per_unit if fee_per_unit else Decimal('0.00')

    # Recent activity log
    recent_activity = []
    latest_payments = all_payments.filter(status='paid').select_related('tenancy__tenant', 'tenancy__unit').order_by('-paid_date')[:3]
    for p in latest_payments:
        recent_activity.append({'type': 'payment', 'text': f'KES {p.amount} received from {p.tenancy.tenant.username} ({p.tenancy.unit.unit_number})', 'time': p.paid_date})
    for t in Tenancy.objects.filter(unit__property__owner=request.user).order_by('-created_at')[:2]:
        recent_activity.append({'type': 'tenant', 'text': f'{t.tenant.username} moved into {t.unit.unit_number}', 'time': t.created_at or t.start_date})
    for i in Inquiry.objects.filter(unit__property__owner=request.user).order_by('-created_at')[:2]:
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

    # Chart: collection trend over last 7 days
    channel_collections = []
    channel_dates = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        channel_dates.append(day.strftime('%a'))
        day_collected = all_payments.filter(status='paid', paid_date=day).aggregate(s=Sum('amount'))['s'] or 0
        channel_collections.append(float(day_collected))

    ctx = {
        'active_tab': 'overview',
        'properties_count': properties.count(),
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'occupancy_rate': occupancy_rate,
        'active_tenancies': active_tenancies,
        'unread_inquiries': unread_inquiries,
        'urgent_maintenance': urgent_maintenance_count,
        'total_collected': total_collected,
        'pending_total': pending_total,
        'overdue_total': overdue_total,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'collection_rate': collection_rate,
        'monthly_collected': monthly_collected,
        'monthly_expected': monthly_expected,
        'sub_status': sub_status,
        'sub': sub,
        'fee_per_unit': fee_per_unit,
        'monthly_sub_fee': monthly_sub_fee,
        'trial_info': trial_info,
        'recent_activity': recent_activity,
        'properties': properties,
        'chart_prop_labels': json.dumps(chart_prop_labels),
        'chart_prop_vacant': json.dumps(chart_prop_vacant),
        'chart_prop_occupied': json.dumps(chart_prop_occupied),
        'type_labels': json.dumps(type_labels),
        'type_counts': json.dumps(type_counts),
        'type_colors': json.dumps(type_colors[:len(type_labels)]),
        'collection_dates': json.dumps(channel_dates),
        'collection_amounts': json.dumps(channel_collections),
        'expiring_leases': expiring_leases,
    }
    return render(request, 'dashboard/overview.html', ctx)


@login_required
def inquiries(request):
    if request.user.profile.role != 'landlord':
        return render(request, 'dashboard/overview.html', {'access_denied': True})
    if not landlord_has_active_sub(request.user):
        return render(request, 'dashboard/locked.html', {'active_tab': 'inquiries'})
    qs = Inquiry.objects.filter(unit__property__owner=request.user).select_related('unit', 'unit__property').order_by('-created_at')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(email__icontains=q) | qs.filter(unit__unit_number__icontains=q)
    read_f = request.GET.get('read', '').strip()
    if read_f == 'unread':
        qs = qs.filter(is_read=False)
    elif read_f == 'read':
        qs = qs.filter(is_read=True)
    if request.GET.get('mark_read'):
        Inquiry.objects.filter(pk=request.GET['mark_read'], unit__property__owner=request.user).update(is_read=True)
        return redirect('dashboard:inquiries')
    page_obj = paginate(request, qs)
    return render(request, 'dashboard/inquiries.html', {'inquiries': page_obj, 'q': q, 'read_f': read_f, 'active_tab': 'inquiries'})
