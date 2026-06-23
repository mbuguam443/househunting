import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
from .models import Tenancy, RentPayment, MaintenanceRequest
from .forms import TenantRegistrationForm, TenancyForm, RentPaymentForm, MarkPaidForm, MaintenanceForm, MaintenanceStatusForm
from .rent_utils import generate_rent_payments, mark_overdue_payments
from .mpesa_utils import stk_push, process_callback
from units.models import Unit

# ==================== LANDLORD VIEWS ====================

@login_required
def register_tenant(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.profile.role = 'tenant'
            user.profile.save()
            messages.success(request, f'Tenant "{user.username}" registered. Now assign them to a unit.')
            return redirect('tenants:create')
    else:
        form = TenantRegistrationForm()
    return render(request, 'tenants/register_tenant.html', {'form': form, 'active_tab': 'tenants'})

@login_required
def tenant_list(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    tenancies = Tenancy.objects.filter(unit__property__owner=request.user).select_related('tenant', 'unit__property')
    return render(request, 'tenants/tenant_list.html', {'tenancies': tenancies, 'active_tab': 'tenants'})

@login_required
def tenant_create(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    if request.method == 'POST':
        form = TenancyForm(request.POST, landlord=request.user)
        if form.is_valid():
            tenancy = form.save()
            tenancy.unit.status = 'occupied'
            tenancy.unit.save()
            generate_rent_payments(landlord=request.user)
            messages.success(request, f'{tenancy.tenant.username} assigned to {tenancy.unit}.')
            return redirect('tenants:list')
    else:
        form = TenancyForm(landlord=request.user)
    return render(request, 'tenants/tenant_create.html', {'form': form, 'active_tab': 'tenants'})

@login_required
def tenant_detail(request, pk):
    tenancy = get_object_or_404(Tenancy.objects.select_related('tenant', 'unit__property'), pk=pk)
    if tenancy.unit.property.owner != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tenants:list')
    payments = tenancy.payments.all()
    return render(request, 'tenants/tenant_detail.html', {'tenancy': tenancy, 'payments': payments, 'active_tab': 'tenants'})

@login_required
def tenant_vacate(request, pk):
    tenancy = get_object_or_404(Tenancy, pk=pk)
    if tenancy.unit.property.owner != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tenants:list')
    if request.method == 'POST':
        tenancy.status = 'ended'
        tenancy.end_date = timezone.now().date()
        tenancy.save()
        tenancy.unit.status = 'vacant'
        tenancy.unit.save()
        messages.success(request, f'{tenancy.tenant.username} vacated. Unit is now available.')
        return redirect('tenants:list')
    return render(request, 'tenants/tenant_vacate.html', {'tenancy': tenancy, 'active_tab': 'tenants'})

@login_required
def rent_collection(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    generate_rent_payments(landlord=request.user)
    mark_overdue_payments(landlord=request.user)
    tenancies = Tenancy.objects.filter(
        unit__property__owner=request.user, status='active'
    ).select_related('tenant', 'unit')
    payments = RentPayment.objects.filter(tenancy__unit__property__owner=request.user).select_related('tenancy__tenant', 'tenancy__unit')
    total_collected = payments.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    pending_count = payments.filter(status='pending').count()
    overdue_count = payments.filter(status='overdue').count()
    return render(request, 'tenants/rent_collection.html', {
        'tenancies': tenancies,
        'payments': payments,
        'total_collected': total_collected,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'active_tab': 'rent',
    })

@login_required
def mark_paid(request, pk):
    payment = get_object_or_404(RentPayment, pk=pk)
    if payment.tenancy.unit.property.owner != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tenants:rent_collection')
    if request.method == 'POST':
        form = MarkPaidForm(request.POST)
        if form.is_valid():
            payment.status = 'paid'
            payment.paid_date = form.cleaned_data['paid_date']
            payment.payment_method = form.cleaned_data['payment_method']
            payment.reference = form.cleaned_data['reference']
            payment.notes = form.cleaned_data['notes']
            payment.save()
            messages.success(request, f'Payment of KES {payment.amount} marked as paid.')
            return redirect('tenants:rent_collection')
    else:
        form = MarkPaidForm(initial={'paid_date': timezone.now().date()})
    return render(request, 'tenants/mark_paid.html', {'payment': payment, 'form': form, 'active_tab': 'rent'})

@login_required
def maintenance_list(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    requests = MaintenanceRequest.objects.filter(
        unit__property__owner=request.user
    ).select_related('tenant', 'unit__property')
    urgent_count = requests.filter(priority='urgent', status__in=['submitted', 'in_progress']).count()
    return render(request, 'tenants/maintenance_list.html', {
        'requests': requests,
        'urgent_count': urgent_count,
        'active_tab': 'maintenance',
    })

@login_required
def maintenance_update(request, pk):
    req = get_object_or_404(MaintenanceRequest, pk=pk)
    if req.unit.property.owner != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tenants:maintenance_list')
    if request.method == 'POST':
        form = MaintenanceStatusForm(request.POST, instance=req)
        if form.is_valid():
            m = form.save(commit=False)
            if m.status in ('resolved', 'closed'):
                m.resolved_at = timezone.now()
            m.save()
            messages.success(request, 'Maintenance request updated.')
            return redirect('tenants:maintenance_list')
    else:
        form = MaintenanceStatusForm(instance=req)
    return render(request, 'tenants/maintenance_update.html', {'req': req, 'form': form, 'active_tab': 'maintenance'})

# ==================== TENANT PORTAL VIEWS ====================

@login_required
def portal_home(request):
    if request.user.profile.role != 'tenant':
        messages.error(request, 'Tenant portal is for tenants only.')
        return redirect('website:home')
    tenancy = Tenancy.objects.filter(tenant=request.user, status='active').select_related('unit__property').first()
    upcoming_payments = RentPayment.objects.filter(tenancy__tenant=request.user, status__in=['pending', 'overdue'])[:5]
    recent_maintenance = MaintenanceRequest.objects.filter(tenant=request.user)[:3]
    return render(request, 'tenants/portal_home.html', {
        'tenancy': tenancy,
        'upcoming_payments': upcoming_payments,
        'recent_maintenance': recent_maintenance,
    })

@login_required
def portal_payments(request):
    if request.user.profile.role != 'tenant':
        messages.error(request, 'Access denied.')
        return redirect('website:home')
    payments = RentPayment.objects.filter(tenancy__tenant=request.user).select_related('tenancy__unit')
    tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
    return render(request, 'tenants/portal_payments.html', {'payments': payments, 'tenancy': tenancy})

@login_required
def portal_pay(request):
    if request.user.profile.role != 'tenant':
        messages.error(request, 'Access denied.')
        return redirect('website:home')
    tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
    if not tenancy:
        messages.error(request, 'You do not have an active tenancy.')
        return redirect('tenants:portal_home')
    if request.method == 'POST':
        form = RentPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.tenancy = tenancy
            payment.status = 'paid' if payment.paid_date else 'pending'
            payment.save()
            messages.success(request, 'Payment recorded successfully.')
            return redirect('tenants:portal_payments')
    else:
        form = RentPaymentForm(initial={
            'amount': tenancy.monthly_rent,
            'due_date': timezone.now().date(),
            'paid_date': timezone.now().date(),
        })
    pending_payments = RentPayment.objects.filter(tenancy=tenancy, status='pending').order_by('due_date')
    mpesa_txs = MpesaTransaction.objects.filter(payment__tenancy=tenancy)[:5]
    return render(request, 'tenants/portal_pay.html', {
        'form': form, 'tenancy': tenancy,
        'pending_payments': pending_payments,
        'mpesa_txs': mpesa_txs,
    })

@login_required
def portal_maintenance(request):
    if request.user.profile.role != 'tenant':
        messages.error(request, 'Access denied.')
        return redirect('website:home')
    requests = MaintenanceRequest.objects.filter(tenant=request.user)
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.tenant = request.user
            tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
            if tenancy:
                m.unit = tenancy.unit
                m.save()
                messages.success(request, 'Maintenance request submitted.')
                return redirect('tenants:portal_maintenance')
            else:
                messages.error(request, 'No active tenancy found.')
    else:
        form = MaintenanceForm()
    return render(request, 'tenants/portal_maintenance.html', {'requests': requests, 'form': form})


# ==================== M-PESA VIEWS ====================

@csrf_exempt
@require_POST
def mpesa_callback(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse('Invalid JSON', status=400)
    success, result = process_callback(data)
    if success:
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
    return JsonResponse({'ResultCode': 1, 'ResultDesc': str(result)})


@login_required
def stk_push_view(request, payment_id):
    if request.user.profile.role != 'tenant':
        return JsonResponse({'error': 'Tenant access required'}, status=403)

    payment = get_object_or_404(RentPayment, pk=payment_id, tenancy__tenant=request.user, status='pending')
    phone = request.POST.get('phone') or request.user.profile.phone

    if not phone:
        return JsonResponse({'error': 'No phone number. Update your profile first.'}, status=400)

    tx, error = stk_push(payment, phone)
    if error:
        return JsonResponse({'error': error}, status=400)
    return JsonResponse({
        'success': True,
        'message': 'STK push sent. Check your phone and enter your M-Pesa PIN.',
        'checkout_id': tx.checkout_request_id,
    })
