import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
from decimal import Decimal
from .models import Tenancy, RentPayment, MaintenanceRequest, MpesaTransaction, LeaseAgreement, C2BTransaction, UtilityBill, B2CTransaction
from .forms import TenantRegistrationForm, TenancyForm, RentPaymentForm, MarkPaidForm, MaintenanceForm, MaintenanceStatusForm, LeaseForm, UtilityBillForm, TenantEditForm
from .b2c_utils import initiate_b2c
from .rent_utils import generate_rent_payments, mark_overdue_payments
from .mpesa_utils import stk_push, process_callback, query_stk_status, _get_access_token
from .c2b_utils import process_c2b_confirmation, process_c2b_validation, register_c2b_urls
from units.models import Unit
from properties.models import Property
from accounts.models import require_landlord_sub
from core.pagination import paginate

DEFAULT_TENANT_PASSWORD = 'password123'

# ==================== LANDLORD VIEWS ====================

@login_required
def register_tenant(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(DEFAULT_TENANT_PASSWORD)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            user.profile.role = 'tenant'
            user.profile.phone = form.cleaned_data['phone']
            user.profile.id_number = form.cleaned_data['id_number']
            user.profile.save()
            messages.success(request, f'Tenant "{user.username}" registered. Password: <strong>{DEFAULT_TENANT_PASSWORD}</strong>. Now assign them to a unit.')
            return redirect('tenants:create')
    else:
        form = TenantRegistrationForm()
    return render(request, 'tenants/register_tenant.html', {'form': form, 'active_tab': 'tenants', 'default_password': DEFAULT_TENANT_PASSWORD})

@login_required
def tenant_list(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    qs = Tenancy.objects.filter(unit__property__owner=request.user).select_related('tenant', 'unit__property')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(tenant__username__icontains=q) | qs.filter(tenant__first_name__icontains=q) | qs.filter(tenant__last_name__icontains=q) | qs.filter(unit__unit_number__icontains=q)
    status_f = request.GET.get('status', '').strip()
    if status_f:
        qs = qs.filter(status=status_f)
    prop_f = request.GET.get('property', '').strip()
    if prop_f:
        qs = qs.filter(unit__property_id=prop_f)
    properties = Property.objects.filter(owner=request.user)
    page_obj = paginate(request, qs)
    return render(request, 'tenants/tenant_list.html', {'tenancies': page_obj, 'q': q, 'status_f': status_f, 'prop_f': prop_f, 'properties': properties, 'active_tab': 'tenants'})

@login_required
def tenant_create(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    units_data = json.dumps(list(Unit.objects.filter(
        property__owner=request.user, status='vacant'
    ).values('id', 'monthly_rent', 'deposit')), default=str)
    if request.method == 'POST':
        form = TenancyForm(request.POST, landlord=request.user)
        if form.is_valid():
            tenancy = form.save(commit=False)
            unit = form.cleaned_data['unit']
            tenancy.monthly_rent = unit.monthly_rent
            tenancy.deposit_paid = unit.deposit or 0
            tenancy.save()
            tenancy.unit.status = 'occupied'
            tenancy.unit.save()
            generate_rent_payments(landlord=request.user)
            messages.success(request, f'{tenancy.tenant.username} assigned to {tenancy.unit}.')
            return redirect('tenants:list')
    else:
        form = TenancyForm(landlord=request.user)
    return render(request, 'tenants/tenant_create.html', {
        'form': form, 'active_tab': 'tenants', 'units_data': units_data
    })

@login_required
def tenant_detail(request, pk):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    tenancy = get_object_or_404(Tenancy.objects.select_related('tenant', 'unit__property'), pk=pk)
    if tenancy.unit.property.owner != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tenants:list')
    tenant_user = tenancy.tenant
    if request.method == 'POST':
        form = TenantEditForm(request.POST, instance=tenant_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'{tenant_user.username} details updated.')
            return redirect('tenants:detail', pk=tenancy.pk)
    else:
        form = TenantEditForm(instance=tenant_user, initial={
            'phone': tenant_user.profile.phone,
            'id_number': tenant_user.profile.id_number,
        })
    payments = tenancy.payments.all()
    balance = payments.exclude(status='paid').exclude(notes='stk_intermediary').aggregate(s=Sum('amount'))['s'] or 0
    q = request.GET.get('q', '').strip()
    if q:
        payments = payments.filter(tenancy__tenant__username__icontains=q) | payments.filter(tenancy__unit__unit_number__icontains=q)
    status_f = request.GET.get('status', '').strip()
    if status_f:
        payments = payments.filter(status=status_f)
    page_obj = paginate(request, payments)
    return render(request, 'tenants/tenant_detail.html', {'tenancy': tenancy, 'payments': page_obj, 'balance': balance, 'q': q, 'status_f': status_f, 'active_tab': 'tenants', 'form': form})

@login_required
def tenant_vacate(request, pk):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
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
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    generate_rent_payments(landlord=request.user)
    mark_overdue_payments(landlord=request.user)
    tenancies = Tenancy.objects.filter(
        unit__property__owner=request.user, status='active'
    ).select_related('tenant', 'unit').prefetch_related('payments')
    payments = RentPayment.objects.filter(tenancy__unit__property__owner=request.user).select_related('tenancy__tenant', 'tenancy__unit')
    total_collected = payments.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    pending_count = payments.filter(status='pending').count()
    overdue_count = payments.filter(status='overdue').count()
    tenancy_balances = {}
    for t in tenancies:
        balance = RentPayment.objects.filter(tenancy=t).exclude(status='paid').exclude(notes='stk_intermediary').aggregate(s=Sum('amount'))['s'] or 0
        tenancy_balances[t.id] = balance
    q = request.GET.get('q', '').strip()
    if q:
        payments = payments.filter(tenancy__tenant__username__icontains=q) | payments.filter(tenancy__unit__unit_number__icontains=q)
    status_f = request.GET.get('status', '').strip()
    if status_f:
        payments = payments.filter(status=status_f)
    page_obj = paginate(request, payments)
    stk_queryable = set(
        MpesaTransaction.objects.filter(
            payment__in=[p.pk for p in page_obj],
            status='pending',
        ).exclude(checkout_request_id='').values_list('payment_id', flat=True)
    )
    return render(request, 'tenants/rent_collection.html', {
        'tenancies': tenancies,
        'payments': page_obj,
        'total_collected': total_collected,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'tenancy_balances': tenancy_balances,
        'q': q, 'status_f': status_f,
        'active_tab': 'rent',
        'stk_queryable': stk_queryable,
    })

@login_required
def mark_paid(request, pk):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    payment = get_object_or_404(RentPayment, pk=pk)
    if payment.tenancy.unit.property.owner != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tenants:rent_collection')
    if request.method == 'POST':
        form = MarkPaidForm(request.POST)
        if form.is_valid():
            paid_amount = form.cleaned_data['amount']
            paid_date = form.cleaned_data['paid_date']
            method = form.cleaned_data['payment_method']
            ref = form.cleaned_data['reference']
            notes = form.cleaned_data['notes']
            tenancy = payment.tenancy
            if paid_amount >= payment.amount:
                payment.status = 'paid'
                payment.paid_date = paid_date
                payment.payment_method = method
                payment.reference = ref
                payment.notes = notes
                payment.save()
                remaining = paid_amount - payment.amount
                invoices = RentPayment.objects.filter(tenancy=tenancy).exclude(status='paid').exclude(pk=payment.pk).order_by('due_date', 'id')
                for inv in invoices:
                    if remaining <= 0:
                        break
                    if inv.amount <= remaining:
                        inv.status = 'paid'
                        inv.paid_date = paid_date
                        inv.payment_method = method
                        inv.reference = ref
                        inv.notes = notes
                        inv.save()
                        remaining -= inv.amount
                    else:
                        inv.amount -= remaining
                        inv.save()
                        remaining = Decimal('0')
                msg = f'Payment of KES {paid_amount} recorded.'
            else:
                payment.amount -= paid_amount
                payment.save()
                msg = f'Partial payment of KES {paid_amount} recorded. Balance: KES {payment.amount}.'
            messages.success(request, msg)
            return redirect('tenants:rent_collection')
    else:
        form = MarkPaidForm(initial={'amount': payment.amount, 'paid_date': timezone.now().date()})
    total_balance = RentPayment.objects.filter(tenancy=payment.tenancy).exclude(status='paid').exclude(notes='stk_intermediary').aggregate(s=Sum('amount'))['s'] or 0
    return render(request, 'tenants/mark_paid.html', {'payment': payment, 'form': form, 'active_tab': 'rent', 'total_balance': total_balance})

@login_required
def maintenance_list(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    qs = MaintenanceRequest.objects.filter(
        unit__property__owner=request.user
    ).select_related('tenant', 'unit__property')
    urgent_count = qs.filter(priority='urgent', status__in=['submitted', 'in_progress']).count()
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(tenant__username__icontains=q) | qs.filter(unit__unit_number__icontains=q) | qs.filter(title__icontains=q)
    status_f = request.GET.get('status', '').strip()
    if status_f:
        qs = qs.filter(status=status_f)
    priority_f = request.GET.get('priority', '').strip()
    if priority_f:
        qs = qs.filter(priority=priority_f)
    page_obj = paginate(request, qs)
    return render(request, 'tenants/maintenance_list.html', {
        'requests': page_obj,
        'urgent_count': urgent_count,
        'q': q, 'status_f': status_f, 'priority_f': priority_f,
        'active_tab': 'maintenance',
    })

@login_required
def maintenance_update(request, pk):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
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
    total_balance = RentPayment.objects.filter(tenancy__tenant=request.user).exclude(status='paid').exclude(notes='stk_intermediary').aggregate(s=Sum('amount'))['s'] or 0
    upcoming_payments = RentPayment.objects.filter(tenancy__tenant=request.user, status__in=['pending', 'overdue'])[:5]
    recent_maintenance = MaintenanceRequest.objects.filter(tenant=request.user)[:3]
    return render(request, 'tenants/portal_home.html', {
        'tenancy': tenancy,
        'total_balance': total_balance,
        'upcoming_payments': upcoming_payments,
        'recent_maintenance': recent_maintenance,
        'active_tab': 'home',
    })

@login_required
def portal_payments(request):
    if request.user.profile.role != 'tenant':
        messages.error(request, 'Access denied.')
        return redirect('website:home')
    qs = RentPayment.objects.filter(tenancy__tenant=request.user).select_related('tenancy__unit').order_by('-created_at')
    payments = paginate(request, qs, per_page=15)
    tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
    total_balance = RentPayment.objects.filter(tenancy__tenant=request.user).exclude(status='paid').exclude(notes='stk_intermediary').aggregate(s=Sum('amount'))['s'] or 0
    return render(request, 'tenants/portal_payments.html', {'payments': payments, 'tenancy': tenancy, 'total_balance': total_balance, 'active_tab': 'payments'})

@login_required
def portal_pay(request):
    if request.user.profile.role != 'tenant':
        messages.error(request, 'Access denied.')
        return redirect('website:home')
    tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
    if not tenancy:
        messages.error(request, 'You do not have an active tenancy.')
        return redirect('tenants:portal_home')
    pending_payments = RentPayment.objects.filter(tenancy=tenancy).exclude(status='paid').exclude(notes='stk_intermediary').order_by('due_date')
    total_balance = RentPayment.objects.filter(tenancy=tenancy).exclude(status='paid').exclude(notes='stk_intermediary').aggregate(s=Sum('amount'))['s'] or 0
    paid_payments = RentPayment.objects.filter(tenancy=tenancy, status='paid').order_by('-paid_date')[:5]
    mpesa_txs = MpesaTransaction.objects.filter(payment__tenancy=tenancy)[:5]
    return render(request, 'tenants/portal_pay.html', {
        'tenancy': tenancy,
        'pending_payments': pending_payments,
        'paid_payments': paid_payments,
        'mpesa_txs': mpesa_txs,
        'total_balance': total_balance,
        'active_tab': 'pay',
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
    return render(request, 'tenants/portal_maintenance.html', {'requests': requests, 'form': form, 'active_tab': 'maintenance'})


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


@csrf_exempt
@require_POST
def c2b_confirmation(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid JSON'}, status=400)
    try:
        result = process_c2b_confirmation(data)
        return JsonResponse(result)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('C2B confirmation error')
        return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)}, status=500)


@csrf_exempt
def c2b_validation(request):
    if request.method == 'GET':
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        try:
            data = request.POST.dict()
        except Exception:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid payload'}, status=400)
    try:
        result = process_c2b_validation(data)
        return JsonResponse(result)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('C2B validation error')
        return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)}, status=500)


@login_required
def register_c2b_view(request):
    if request.user.profile.role not in ('admin', 'landlord'):
        return JsonResponse({'error': 'Access denied'}, status=403)
    landlord_id = request.POST.get('landlord_id') or request.GET.get('landlord_id') or request.user.id
    from django.contrib.auth.models import User
    landlord = get_object_or_404(User, pk=landlord_id)

    if request.method == 'POST':
        for field in ['mpesa_consumer_key', 'mpesa_consumer_secret', 'mpesa_passkey', 'mpesa_shortcode', 'c2b_shortcode', 'mpesa_callback_url', 'c2b_confirmation_url', 'c2b_validation_url']:
            val = request.POST.get(field, '').strip()
            setattr(landlord.profile, field, val)
        landlord.profile.save()

    result = register_c2b_urls(landlord)
    return JsonResponse(result)


@login_required
def check_payment_status(request):
    payment_id = request.GET.get('payment_id')
    if not payment_id:
        return JsonResponse({'error': 'payment_id required'}, status=400)
    try:
        pmt = RentPayment.objects.get(pk=payment_id, tenancy__tenant=request.user)
    except RentPayment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    tx = MpesaTransaction.objects.filter(payment=pmt).first()
    return JsonResponse({
        'payment_id': pmt.id,
        'payment_status': pmt.status,
        'mpesa_status': tx.status if tx else None,
        'receipt': pmt.reference,
        'amount': str(pmt.amount),
    })

@login_required
def query_stk_push(request, payment_id):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    payment = get_object_or_404(RentPayment, pk=payment_id)
    if payment.tenancy.unit.property.owner != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tenants:rent_collection')
    tx = MpesaTransaction.objects.filter(payment=payment, status='pending').exclude(checkout_request_id='').first()
    if not tx:
        messages.info(request, 'No pending STK push to query for this payment.')
        return redirect('tenants:rent_collection')
    data = query_stk_status(tx.checkout_request_id)
    if data.get('ResponseCode') != '0':
        messages.warning(request, f"M-Pesa query failed: {data.get('ResponseDescription', 'Unknown error')}")
        return redirect('tenants:rent_collection')
    result_code = data.get('ResultCode')
    result_desc = data.get('ResultDesc', '')
    tx.result_code = str(result_code) if result_code is not None else ''
    tx.result_desc = result_desc
    tx.raw_callback = data
    if result_code == '0':
        tx.status = 'completed'
        tx.save()
        payment.status = 'paid'
        payment.paid_date = timezone.now().date()
        payment.reference = data.get('ReceiptNumber', '')
        payment.save()
        messages.success(request, f'STK query confirmed payment of KES {payment.amount}. Payment marked as paid.')
    else:
        tx.status = 'failed'
        tx.save()
        messages.warning(request, f'STK query returned: {result_desc}')
    return redirect('tenants:rent_collection')


@login_required
def stk_push_view(request):
    if request.user.profile.role != 'tenant':
        return JsonResponse({'error': 'Tenant access required'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
    if not tenancy:
        return JsonResponse({'error': 'No active tenancy'}, status=400)

    try:
        amount = Decimal(request.POST.get('amount', '0'))
    except Exception:
        return JsonResponse({'error': 'Invalid amount'}, status=400)

    if amount <= 0:
        return JsonResponse({'error': 'Amount must be greater than 0'}, status=400)

    phone = request.POST.get('phone') or request.user.profile.phone

    if not phone:
        return JsonResponse({'error': 'No phone number. Update your profile first.'}, status=400)

    landlord = tenancy.unit.property.owner

    payment = RentPayment.objects.create(
        tenancy=tenancy, amount=amount, due_date=timezone.now().date(), status='pending', notes='stk_intermediary'
    )

    tx, error = stk_push(payment, phone, landlord)
    if error:
        payment.delete()
        return JsonResponse({'error': error}, status=400)
    return JsonResponse({
        'success': True,
        'message': 'STK push sent. Check your phone and enter your M-Pesa PIN.',
        'payment_id': payment.id,
        'checkout_id': tx.checkout_request_id,
    })


# ---- Lease Views ----

@login_required
def lease_create(request, tenancy_pk):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Access denied.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    tenancy = get_object_or_404(Tenancy, pk=tenancy_pk)
    if tenancy.unit.property.owner != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tenants:list')
    if hasattr(tenancy, 'lease'):
        messages.warning(request, 'A lease already exists for this tenancy.')
        return redirect('tenants:lease_detail', pk=tenancy.lease.pk)
    if request.method == 'POST':
        form = LeaseForm(request.POST)
        if form.is_valid():
            lease = form.save(commit=False)
            lease.tenancy = tenancy
            lease.status = 'active'
            lease.landlord_accepted = True
            lease.landlord_accepted_at = timezone.now()
            lease.save()
            messages.success(request, f'Lease created for {tenancy.tenant.username}.')
            return redirect('tenants:lease_detail', pk=lease.pk)
    else:
        form = LeaseForm(initial={
            'start_date': tenancy.start_date,
            'end_date': tenancy.end_date or (tenancy.start_date + timedelta(days=365)),
            'monthly_rent': tenancy.monthly_rent,
            'deposit_amount': tenancy.deposit_paid,
        })
    return render(request, 'tenants/lease_form.html', {'form': form, 'tenancy': tenancy, 'active_tab': 'tenants'})


@login_required
def lease_detail(request, pk):
    lease = get_object_or_404(LeaseAgreement.objects.select_related('tenancy__tenant', 'tenancy__unit__property'), pk=pk)
    if request.user.profile.role == 'landlord':
        if lease.tenancy.unit.property.owner != request.user:
            messages.error(request, 'Access denied.')
            return redirect('website:home')
    elif request.user.profile.role == 'tenant':
        if lease.tenancy.tenant != request.user:
            messages.error(request, 'Access denied.')
            return redirect('portal:home')
    else:
        return redirect('website:home')
    return render(request, 'tenants/lease_detail.html', {'lease': lease, 'active_tab': 'tenants'})


@login_required
def lease_accept(request, pk):
    lease = get_object_or_404(LeaseAgreement, pk=pk)
    if request.user != lease.tenancy.tenant:
        messages.error(request, 'Access denied.')
        return redirect('portal:home')
    if lease.tenant_accepted:
        messages.info(request, 'You have already accepted this lease.')
        return redirect('tenants:lease_detail', pk=lease.pk)
    if request.method == 'POST':
        lease.tenant_accepted = True
        lease.tenant_accepted_at = timezone.now()
        lease.save()
        messages.success(request, 'Lease accepted successfully.')
        return redirect('tenants:lease_detail', pk=lease.pk)
    return render(request, 'tenants/lease_accept.html', {'lease': lease})


@login_required
def lease_terminate(request, pk):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Access denied.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    lease = get_object_or_404(LeaseAgreement, pk=pk)
    if lease.tenancy.unit.property.owner != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tenants:list')
    if request.method == 'POST':
        lease.status = 'terminated'
        lease.save()
        lease.tenancy.status = 'ended'
        lease.tenancy.end_date = timezone.now().date()
        lease.tenancy.save()
        lease.tenancy.unit.status = 'vacant'
        lease.tenancy.unit.save()
        messages.success(request, 'Lease terminated. Unit is now vacant.')
        return redirect('tenants:lease_detail', pk=lease.pk)
    return render(request, 'tenants/lease_terminate.html', {'lease': lease})


@login_required
def record_payment(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp

    from .forms import RecordPaymentForm
    if request.method == 'POST':
        form = RecordPaymentForm(request.POST, landlord=request.user)
        if form.is_valid():
            tenancy = form.cleaned_data['tenancy']
            amount = form.cleaned_data['amount']
            paid_date = form.cleaned_data['paid_date']
            method = form.cleaned_data['payment_method']
            ref = form.cleaned_data['reference']
            notes = form.cleaned_data['notes']

            paid_amount = Decimal(str(amount))

            pmt = RentPayment.objects.create(
                tenancy=tenancy,
                amount=paid_amount,
                due_date=paid_date,
                paid_date=paid_date,
                status='paid',
                payment_method=method,
                reference=ref or '',
                notes=notes or f'Manual payment recorded by {request.user.username}',
            )

            invoices = RentPayment.objects.filter(tenancy=tenancy).exclude(status='paid').exclude(pk=pmt.pk).order_by('due_date', 'id')
            remaining = paid_amount
            for inv in invoices:
                if remaining <= 0:
                    break
                if inv.amount <= remaining:
                    inv.status = 'paid'
                    inv.paid_date = paid_date
                    inv.payment_method = method
                    inv.reference = ref or ''
                    if notes:
                        inv.notes = notes
                    inv.save()
                    remaining -= inv.amount
                else:
                    inv.amount -= remaining
                    inv.save()
                    remaining = Decimal('0')

            messages.success(request, f'Payment of KES {amount} recorded for {tenancy.tenant.username} @ {tenancy.unit.unit_number}.')
            return redirect('tenants:reports')
    else:
        form = RecordPaymentForm(landlord=request.user, initial={'paid_date': timezone.now().date()})

    return render(request, 'tenants/record_payment.html', {'form': form, 'active_tab': 'record_payment'})


@login_required
def c2b_transactions(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp

    qs = C2BTransaction.objects.all().order_by('-created_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(bill_ref__icontains=q) |
            Q(trans_id__icontains=q) |
            Q(phone__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(matched_tenant__username__icontains=q)
        )

    page_obj = paginate(request, qs)
    return render(request, 'tenants/c2b_transactions.html', {
        'transactions': page_obj,
        'q': q,
        'active_tab': 'c2b',
    })


@login_required
def reports(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp

    tab = request.GET.get('tab', 'transactions')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    tenant_q = request.GET.get('tenant', '')

    base_qs = RentPayment.objects.filter(tenancy__unit__property__owner=request.user).select_related('tenancy__tenant', 'tenancy__unit')

    if date_from:
        base_qs = base_qs.filter(due_date__gte=date_from)
    if date_to:
        base_qs = base_qs.filter(due_date__lte=date_to)
    if tenant_q:
        base_qs = base_qs.filter(
            Q(tenancy__tenant__username__icontains=tenant_q) |
            Q(tenancy__unit__unit_number__icontains=tenant_q)
        )

    if tab == 'transactions':
        qs = base_qs.filter(status='paid').order_by('-paid_date', '-created_at')
        total = qs.aggregate(s=Sum('amount'))['s'] or 0
    else:
        qs = base_qs.exclude(status='paid').order_by('-created_at')
        total = qs.aggregate(s=Sum('amount'))['s'] or 0

    page_obj = paginate(request, qs, per_page=20)
    properties = Property.objects.filter(owner=request.user)

    return render(request, 'tenants/reports.html', {
        'records': page_obj,
        'tab': tab,
        'total': total,
        'date_from': date_from,
        'date_to': date_to,
        'tenant_q': tenant_q,
        'properties': properties,
        'active_tab': 'reports',
    })


# ---- Utility Bill Views ----

@login_required
def utility_list(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    qs = UtilityBill.objects.filter(tenancy__unit__property__owner=request.user).select_related('tenancy__tenant', 'tenancy__unit').order_by('-created_at')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(tenancy__tenant__username__icontains=q) | Q(tenancy__unit__unit_number__icontains=q))
    type_f = request.GET.get('type', '').strip()
    if type_f:
        qs = qs.filter(utility_type=type_f)
    status_f = request.GET.get('status', '').strip()
    if status_f:
        qs = qs.filter(status=status_f)
    page_obj = paginate(request, qs, per_page=20)
    return render(request, 'tenants/utility_list.html', {
        'bills': page_obj, 'q': q, 'type_f': type_f, 'status_f': status_f, 'active_tab': 'utilities',
    })

@login_required
def utility_add(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    if request.method == 'POST':
        form = UtilityBillForm(request.user, request.POST)
        if form.is_valid():
            tenancy = form.cleaned_data.get('tenancy')
            bill_all = form.cleaned_data.get('bill_all')
            prop = form.cleaned_data.get('property')

            if bill_all and prop:
                tenancies = Tenancy.objects.filter(unit__property=prop, status='active')
                if not tenancies.exists():
                    messages.error(request, 'No active tenancies in this property.')
                    props = Property.objects.filter(owner=request.user).values('id', 'name', 'water_rate', 'electricity_rate', 'trash_rate')
                    property_rates = json.dumps({str(p['id']): {'name': p['name'], 'water_rate': float(p['water_rate']), 'electricity_rate': float(p['electricity_rate']), 'trash_rate': float(p['trash_rate'])} for p in props})
                    return render(request, 'tenants/utility_add.html', {'form': form, 'edit': False, 'property_rates': property_rates, 'active_tab': 'utilities'})
                count = 0
                for t in tenancies:
                    ub = form.save(commit=False)
                    ub.tenancy = t
                    ub.save()
                    RentPayment.objects.create(
                        tenancy=t,
                        amount=ub.amount,
                        due_date=ub.due_date,
                        status='pending',
                        payment_method='utility',
                        reference=f'{ub.get_utility_type_display()}-{ub.pk}',
                        notes=f'Utility bill: {ub.get_utility_type_display()} ({ub.period_start} - {ub.period_end})',
                        utility_bill=ub,
                    )
                    count += 1
                messages.success(request, f'Utility bills added for {count} tenant(s) in {prop.name}.')
            elif tenancy:
                ub = form.save(commit=False)
                ub.tenancy = tenancy
                ub.save()
                RentPayment.objects.create(
                    tenancy=tenancy,
                    amount=ub.amount,
                    due_date=ub.due_date,
                    status='pending',
                    payment_method='utility',
                    reference=f'{ub.get_utility_type_display()}-{ub.pk}',
                    notes=f'Utility bill: {ub.get_utility_type_display()} ({ub.period_start} - {ub.period_end})',
                    utility_bill=ub,
                )
                messages.success(request, 'Utility bill added successfully.')
            return redirect('tenants:utility_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UtilityBillForm(request.user)
    props = Property.objects.filter(owner=request.user).values('id', 'name', 'water_rate', 'electricity_rate', 'trash_rate')
    property_rates = json.dumps({str(p['id']): {'name': p['name'], 'water_rate': float(p['water_rate']), 'electricity_rate': float(p['electricity_rate']), 'trash_rate': float(p['trash_rate'])} for p in props})
    return render(request, 'tenants/utility_add.html', {'form': form, 'edit': False, 'property_rates': property_rates, 'active_tab': 'utilities'})

@login_required
def utility_mark_paid(request, pk):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    ub = get_object_or_404(UtilityBill, pk=pk, tenancy__unit__property__owner=request.user)
    rp = ub.rent_payment if hasattr(ub, 'rent_payment') else None
    if ub.status == 'paid':
        ub.status = 'pending'
        ub.paid_date = None
        ub.payment_method = ''
        ub.reference = ''
        if rp:
            rp.status = 'pending'
            rp.paid_date = None
            rp.save()
    else:
        ub.status = 'paid'
        ub.paid_date = timezone.now()
        if rp:
            rp.status = 'paid'
            rp.paid_date = timezone.now().date()
            rp.save()
    ub.save()
    return redirect('tenants:utility_list')

@login_required
def utility_edit(request, pk):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    ub = get_object_or_404(UtilityBill, pk=pk, tenancy__unit__property__owner=request.user)
    if request.method == 'POST':
        form = UtilityBillForm(request.user, request.POST, instance=ub)
        if form.is_valid():
            form.save()
            rp = ub.rent_payment if hasattr(ub, 'rent_payment') else None
            if rp:
                rp.amount = ub.amount
                rp.due_date = ub.due_date
                rp.save()
            messages.success(request, 'Utility bill updated.')
            return redirect('tenants:utility_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UtilityBillForm(request.user, instance=ub)
    return render(request, 'tenants/utility_add.html', {'form': form, 'edit': True, 'active_tab': 'utilities'})

@login_required
def utility_delete(request, pk):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    ub = get_object_or_404(UtilityBill, pk=pk, tenancy__unit__property__owner=request.user)
    rp = ub.rent_payment if hasattr(ub, 'rent_payment') else None
    if rp:
        rp.delete()
    ub.delete()
    messages.success(request, 'Utility bill deleted.')
    return redirect('tenants:utility_list')

# ---- B2C Commission Payment Views ----

@login_required
def b2c_pay(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp

    # Get admin's phone for recipient
    from django.contrib.auth.models import User
    admin = User.objects.filter(profile__role='admin').first()
    admin_phone = admin.profile.phone if admin and admin.profile.phone else ''

    if request.method == 'POST':
        password = request.POST.get('password', '')
        amount = request.POST.get('amount', '')

        if not request.user.check_password(password):
            messages.error(request, 'Incorrect password. Transaction cancelled.')
            return redirect('tenants:b2c_pay')

        if not amount:
            messages.error(request, 'Enter an amount.')
            return redirect('tenants:b2c_pay')

        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError
        except:
            messages.error(request, 'Invalid amount.')
            return redirect('tenants:b2c_pay')

        if not (request.user.profile.b2c_shortcode or request.user.profile.c2b_shortcode):
            messages.error(request, 'No B2C paybill configured. Set it up in B2C Settings first.')
            return redirect('tenants:b2c_pay')

        if not request.user.profile.b2c_initiator_name or not request.user.profile.b2c_initiator_password:
            messages.error(request, 'B2C initiator credentials not configured. Set them up in your profile first.')
            return redirect('tenants:b2c_pay')

        if not admin_phone:
            messages.error(request, 'Admin has no phone number configured. Contact support.')
            return redirect('tenants:b2c_pay')

        tx, error = initiate_b2c(request.user, amount, admin_phone, admin.username if admin else 'Admin')
        if error:
            messages.error(request, f'B2C failed: {error}')
        else:
            messages.success(request, f'KES {amount} sent successfully! Reference: {tx.transaction_id or tx.conversation_id}')
        return redirect('tenants:b2c_history')

    # Calculate suggested amount from fee_per_unit
    from accounts.models import get_fee_per_unit
    unit_count = Tenancy.objects.filter(unit__property__owner=request.user, status='active').count()
    fee = get_fee_per_unit(request.user)
    suggested = unit_count * fee

    return render(request, 'tenants/b2c_pay.html', {
        'suggested': suggested,
        'admin_phone': admin_phone,
        'admin_name': admin.username if admin else 'Admin',
        'active_tab': 'b2c',
    })


@csrf_exempt
def b2c_result(request):
    """Callback from Safaricom for B2C transaction result."""
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
        # Safaricom wraps result in a "Result" object
        result = data.get('Result', data)
        conv_id = result.get('ConversationID', data.get('ConversationID', ''))
        if conv_id:
            tx = B2CTransaction.objects.filter(conversation_id=conv_id).first()
            if not tx:
                tx = B2CTransaction.objects.filter(originator_conversation_id=result.get('OriginatorConversationID', '')).first()
            if tx:
                tx.raw_response = data
                tx.result_code = result.get('ResultCode')
                tx.response_description = result.get('ResultDesc', result.get('ResponseDescription', ''))
                tx.transaction_id = tx.transaction_id or result.get('TransactionID', '')

                # Parse ResultParameters array
                params = result.get('ResultParameters', {})
                param_list = params.get('ResultParameter', []) if isinstance(params, dict) else []
                for p in param_list:
                    key = p.get('Key', '')
                    val = p.get('Value', '')
                    if key == 'TransactionReceipt':
                        tx.transaction_receipt = str(val)
                    elif key == 'ReceiverPartyPublicName':
                        tx.receiver_public_name = str(val)
                    elif key == 'TransactionCompletedDateTime':
                        tx.completed_at = str(val)
                    elif key == 'B2CChargesPaidAccountAvailableFunds':
                        try:
                            tx.b2c_charges = Decimal(str(val))
                        except Exception:
                            pass

                if tx.result_code == 0:
                    tx.status = 'completed'
                else:
                    tx.status = 'failed'
                tx.save()
    except Exception:
        pass
    return HttpResponse(status=200)


@csrf_exempt
def b2c_timeout(request):
    """Callback from Safaricom for B2C transaction timeout."""
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
        result = data.get('Result', data)
        conv_id = result.get('ConversationID', data.get('ConversationID', ''))
        if conv_id:
            tx = B2CTransaction.objects.filter(conversation_id=conv_id).first()
            if tx:
                tx.raw_response = data
                tx.result_code = result.get('ResultCode')
                tx.response_description = result.get('ResultDesc', 'B2C request timed out')
                tx.status = 'failed'
                tx.save()
    except Exception:
        pass
    return HttpResponse(status=200)


@login_required
def b2c_history(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    qs = B2CTransaction.objects.filter(landlord=request.user).order_by('-created_at')
    page_obj = paginate(request, qs, per_page=20)
    return render(request, 'tenants/b2c_history.html', {
        'transactions': page_obj, 'active_tab': 'b2c',
    })


@login_required
def b2c_settings(request):
    if request.user.profile.role != 'landlord':
        messages.error(request, 'Landlord access required.')
        return redirect('website:home')
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp

    if request.method == 'POST':
        pwd = request.POST.get('password', '')
        if not request.user.check_password(pwd):
            messages.error(request, 'Incorrect password.')
            return redirect('tenants:b2c_settings')

        for field in ['b2c_shortcode', 'b2c_initiator_name', 'b2c_initiator_password', 'b2c_callback_base_url']:
            val = request.POST.get(field, '').strip()
            setattr(request.user.profile, field, val)
        request.user.profile.save()
        messages.success(request, 'B2C settings saved.')
        return redirect('tenants:b2c_settings')

    return render(request, 'tenants/b2c_settings.html', {
        'active_tab': 'b2c',
    })


# ---- Tenant Portal Utility Views ----

@login_required
def portal_utilities(request):
    if request.user.profile.role != 'tenant':
        return redirect('website:home')
    tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
    bills = UtilityBill.objects.filter(tenancy=tenancy).order_by('-created_at') if tenancy else []
    return render(request, 'tenants/portal_utilities.html', {
        'bills': bills, 'tenancy': tenancy, 'active_tab': 'utilities',
    })

# ---- Tenant Portal Lease Views ----

@login_required
def portal_lease(request):
    if request.user.profile.role != 'tenant':
        return redirect('website:home')
    tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
    lease = getattr(tenancy, 'lease', None) if tenancy else None
    return render(request, 'tenants/portal_lease.html', {'lease': lease, 'tenancy': tenancy, 'active_tab': 'lease'})
