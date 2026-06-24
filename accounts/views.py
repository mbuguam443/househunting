from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import date, timedelta
from .forms import RegistrationForm, ProfileForm, UserForm
from .models import Profile, SubscriptionPlan, LandlordSubscription, PlatformConfig, get_fee_per_unit
from properties.models import Property
from units.models import Unit
from tenants.models import Tenancy, RentPayment

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = user.profile
            profile.role = form.cleaned_data['role']
            profile.save()
            login(request, user)
            messages.success(request, f'Welcome to PataNyumba, {user.username}!')
            if profile.role == 'landlord':
                return redirect('dashboard:overview')
            if profile.role == 'tenant':
                return redirect('portal:home')
            return redirect('website:home')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if hasattr(user, 'profile'):
                if user.profile.role == 'admin':
                    return redirect('accounts:admin_dashboard')
                if user.profile.role == 'landlord':
                    return redirect('dashboard:overview')
                if user.profile.role == 'tenant':
                    return redirect('portal:home')
            return redirect('website:home')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('website:home')

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    template = 'accounts/dashboard_profile.html' if request.user.profile.role == 'landlord' else 'accounts/profile.html'
    return render(request, template, {
        'user_form': user_form, 'profile_form': profile_form, 'active_tab': 'profile'
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


# ==================== ADMIN PORTAL ====================

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and hasattr(user, 'profile') and user.profile.role == 'admin':
            login(request, user)
            return redirect('accounts:admin_dashboard')
        messages.error(request, 'Invalid credentials or not an admin.')
    return render(request, 'accounts/admin_login.html')


@login_required
def admin_dashboard(request):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    landlord_count = Profile.objects.filter(role='landlord').count()
    tenant_count = Profile.objects.filter(role='tenant').count()
    prop_count = Property.objects.count()
    unit_count = Unit.objects.count()
    active_subs = LandlordSubscription.objects.filter(status='active').count()
    expired_subs = LandlordSubscription.objects.filter(status='expired').count()
    sub_revenue = LandlordSubscription.objects.filter(status='active').aggregate(s=Sum('amount'))['s'] or 0
    fee = get_fee_per_unit()
    from website.models import Inquiry
    contact_inquiries = Inquiry.objects.filter(unit__isnull=True).order_by('-created_at')[:6]
    return render(request, 'accounts/admin_dashboard.html', {
        'landlord_count': landlord_count, 'tenant_count': tenant_count,
        'prop_count': prop_count, 'unit_count': unit_count,
        'active_subs': active_subs, 'expired_subs': expired_subs,
        'sub_revenue': sub_revenue, 'fee_per_unit': fee,
        'contact_inquiries': contact_inquiries,
    })


@login_required
def admin_landlords(request):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    landlords = Profile.objects.filter(role='landlord').select_related('user').prefetch_related('user__subscriptions')
    for p in landlords:
        p.unit_count = Unit.objects.filter(property__owner=p.user).count()
        landlord_fee = get_fee_per_unit(p.user)
        p.monthly_fee = p.unit_count * landlord_fee
    return render(request, 'accounts/admin_landlords.html', {'landlords': landlords})


@login_required
def admin_set_landlord_fee(request, landlord_id):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    landlord = get_object_or_404(User, pk=landlord_id, profile__role='landlord')
    if request.method == 'POST':
        fee = request.POST.get('fee_per_unit')
        if fee is not None:
            landlord.profile.fee_per_unit = fee
            landlord.profile.save()
            messages.success(request, f'Fee for {landlord.username} set to KES {fee}/unit.')
        return redirect('accounts:admin_landlords')
    return redirect('accounts:admin_landlords')


@login_required
def admin_create_landlord(request):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.profile.role = 'landlord'
            user.profile.phone = request.POST.get('phone', '')
            user.profile.save()
            messages.success(request, f'Landlord "{user.username}" created.')
            return redirect('accounts:admin_landlords')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/admin_landlord_form.html', {'form': form, 'title': 'Create Landlord'})


@login_required
def admin_subscription_plans(request):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    config, _ = PlatformConfig.objects.get_or_create(pk=1, defaults={'fee_per_unit': 50.00})
    plans = SubscriptionPlan.objects.all()
    return render(request, 'accounts/admin_plans.html', {'config': config, 'plans': plans})


@login_required
def admin_plan_create(request):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    if request.method == 'POST':
        name = request.POST.get('name')
        amount = request.POST.get('amount')
        duration = request.POST.get('duration_days')
        desc = request.POST.get('description', '')
        if name and amount and duration:
            SubscriptionPlan.objects.create(name=name, amount=amount, duration_days=duration, description=desc)
            messages.success(request, 'Plan created.')
            return redirect('accounts:admin_plans')
        messages.error(request, 'All fields required.')
    return render(request, 'accounts/admin_plan_form.html', {'title': 'Add Plan'})


@login_required
def admin_plan_toggle(request, pk):
    if request.user.profile.role != 'admin':
        return redirect('website:home')
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    plan.is_active = not plan.is_active
    plan.save()
    messages.success(request, f'Plan {"activated" if plan.is_active else "deactivated"}.')
    return redirect('accounts:admin_plans')


@login_required
def admin_update_fee(request):
    if request.user.profile.role != 'admin':
        return redirect('website:home')
    if request.method == 'POST':
        fee = request.POST.get('fee_per_unit')
        if fee:
            config, _ = PlatformConfig.objects.get_or_create(pk=1)
            config.fee_per_unit = fee
            config.save()
            messages.success(request, f'Fee updated to KES {fee}/unit/month.')
    return redirect('accounts:admin_plans')


@login_required
def admin_assign_subscription(request, landlord_id):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    landlord = get_object_or_404(User, pk=landlord_id, profile__role='landlord')
    fee = get_fee_per_unit(landlord)
    unit_count = Unit.objects.filter(property__owner=landlord).count()
    monthly_fee = unit_count * fee
    if request.method == 'POST':
        months = int(request.POST.get('months', 1))
        ref = request.POST.get('payment_reference', '')
        total = monthly_fee * months
        LandlordSubscription.objects.create(
            landlord=landlord, unit_count=unit_count, amount=total,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30 * months),
            status='active', payment_reference=ref,
            notes=f'{unit_count} units × KES {fee}/unit × {months} month(s)',
        )
        messages.success(request, f'{months}-month subscription for KES {total} assigned to {landlord.username}.')
        return redirect('accounts:admin_landlords')
    return render(request, 'accounts/admin_assign_sub.html', {
        'landlord': landlord, 'fee_per_unit': fee,
        'unit_count': unit_count, 'monthly_fee': monthly_fee,
    })
