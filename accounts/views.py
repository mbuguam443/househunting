from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .forms import ProfileForm, UserForm
from .models import Profile, SubscriptionPlan, LandlordSubscription, PlatformConfig, get_fee_per_unit, landlord_trial_info
from core.pagination import paginate
from properties.models import Property
from units.models import Unit
from tenants.models import Tenancy, RentPayment

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
    ctx = {'user_form': user_form, 'profile_form': profile_form, 'active_tab': 'profile'}
    if request.user.profile.role == 'landlord':
        from units.models import Unit
        from accounts.models import LandlordSubscription, get_fee_per_unit
        unit_count = Unit.objects.filter(property__owner=request.user).count()
        fee = request.user.profile.fee_per_unit if request.user.profile.fee_per_unit else get_fee_per_unit()
        ctx['sub_fee_per_unit'] = fee
        ctx['sub_unit_count'] = unit_count
        ctx['sub_monthly_total'] = fee * unit_count
        ctx['sub_status'] = LandlordSubscription.objects.filter(landlord=request.user).order_by('-end_date').first()
    template = 'accounts/dashboard_profile.html' if request.user.profile.role == 'landlord' else 'accounts/profile.html'
    return render(request, template, ctx)

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
    qs = Profile.objects.filter(role='landlord').select_related('user').prefetch_related('user__subscriptions')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(user__username__icontains=q) | qs.filter(user__first_name__icontains=q) | qs.filter(user__last_name__icontains=q) | qs.filter(phone__icontains=q)
        qs = qs.distinct()
    for p in qs:
        p.unit_count = Unit.objects.filter(property__owner=p.user).count()
        landlord_fee = get_fee_per_unit(p.user)
        p.monthly_fee = p.unit_count * landlord_fee
        p.trial_info_val = landlord_trial_info(p.user)
        p.mpesa_set = bool(p.mpesa_shortcode)
    page_obj = paginate(request, qs)
    return render(request, 'accounts/admin_landlords.html', {'landlords': page_obj, 'q': q})


@login_required
def admin_set_landlord_fee(request, landlord_id):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    landlord = get_object_or_404(User, pk=landlord_id, profile__role='landlord')
    if request.method == 'POST':
        raw = request.POST.get('fee_per_unit', '').strip()
        try:
            fee = Decimal(raw)
        except Exception:
            messages.error(request, 'Invalid fee value.')
            return redirect('accounts:admin_landlords')
        if fee < 0:
            messages.error(request, 'Fee cannot be negative.')
            return redirect('accounts:admin_landlords')
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
            user.profile.trial_started_at = timezone.now()
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
def admin_revenue(request):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    subs = LandlordSubscription.objects.select_related('landlord').order_by('-created_at')
    q = request.GET.get('q', '').strip()
    if q:
        subs = subs.filter(landlord__username__icontains=q)
    status_f = request.GET.get('status', '').strip()
    if status_f:
        subs = subs.filter(status=status_f)
    total_collected = LandlordSubscription.objects.aggregate(s=Sum('amount'))['s'] or 0
    active_revenue = LandlordSubscription.objects.filter(status='active').aggregate(s=Sum('amount'))['s'] or 0
    active_count = LandlordSubscription.objects.filter(status='active').count()
    expired_count = LandlordSubscription.objects.filter(status='expired').count()
    page_obj = paginate(request, subs)
    return render(request, 'accounts/admin_revenue.html', {
        'subscriptions': page_obj,
        'total_collected': total_collected,
        'active_revenue': active_revenue,
        'active_count': active_count,
        'expired_count': expired_count,
        'landlord_count': Profile.objects.filter(role='landlord').count(),
        'q': q, 'status_f': status_f,
        'active_tab': 'revenue',
    })


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


@login_required
def admin_landlord_mpesa(request, landlord_id):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    landlord = get_object_or_404(User, pk=landlord_id, profile__role='landlord')
    if request.method == 'POST':
        for field in ['mpesa_consumer_key', 'mpesa_consumer_secret', 'mpesa_passkey', 'mpesa_shortcode', 'c2b_shortcode', 'mpesa_callback_url', 'c2b_confirmation_url', 'c2b_validation_url']:
            val = request.POST.get(field, '').strip()
            setattr(landlord.profile, field, val)
        landlord.profile.save()
        messages.success(request, f'M-Pesa credentials updated for {landlord.username}.')
        return redirect('accounts:admin_landlords')
    return render(request, 'accounts/admin_landlord_mpesa.html', {'landlord': landlord})


# ==================== ADMIN LISTINGS (Independent House Hunting) ====================

@login_required
def admin_listings(request):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    from website.models import AdminListing
    qs = AdminListing.objects.select_related('created_by').all()
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(county__icontains=q) | qs.filter(town__icontains=q) | qs.filter(estate__icontains=q)
    status_f = request.GET.get('status', '').strip()
    if status_f:
        qs = qs.filter(status=status_f)
    page_obj = paginate(request, qs)
    return render(request, 'accounts/admin_listings.html', {'listings': page_obj, 'q': q, 'status_f': status_f})


@login_required
def admin_listing_create(request):
    if request.user.profile.role != 'admin':
        return redirect('website:home')
    if request.method == 'POST':
        from website.models import AdminListing
        from core.models import HouseType
        title = request.POST.get('title')
        desc = request.POST.get('description')
        county = request.POST.get('county')
        town = request.POST.get('town')
        estate = request.POST.get('estate', '')
        house_type_slug = request.POST.get('house_type')
        bedrooms = int(request.POST.get('bedrooms', 1))
        bathrooms = int(request.POST.get('bathrooms', 1))
        rent = request.POST.get('rent')
        contact_name = request.POST.get('contact_name', '')
        contact_phone = request.POST.get('contact_phone', '')
        image = request.FILES.get('image')
        extra_images = request.FILES.getlist('extra_images')
        if title and desc and county and town and rent:
            ht = HouseType.objects.filter(slug=house_type_slug).first()
            listing = AdminListing.objects.create(
                title=title, description=desc, county=county, town=town, estate=estate,
                house_type=ht, bedrooms=bedrooms, bathrooms=bathrooms, rent=rent,
                contact_name=contact_name, contact_phone=contact_phone, image=image,
                created_by=request.user,
            )
            for i, img in enumerate(extra_images):
                listing.images.create(image=img, order=i)
            messages.success(request, 'Listing created and visible on the public site.')
            return redirect('accounts:admin_listings')
        messages.error(request, 'Title, description, county, town, and rent are required.')
    from core.models import HouseType
    return render(request, 'accounts/admin_listing_form.html', {'title': 'New Listing', 'house_types': HouseType.objects.all()})


@login_required
def admin_listing_edit(request, pk):
    if request.user.profile.role != 'admin':
        return redirect('website:home')
    from website.models import AdminListing
    listing = get_object_or_404(AdminListing, pk=pk)
    if request.method == 'POST':
        from core.models import HouseType
        listing.title = request.POST.get('title')
        listing.description = request.POST.get('description')
        listing.county = request.POST.get('county')
        listing.town = request.POST.get('town')
        listing.estate = request.POST.get('estate', '')
        listing.house_type = HouseType.objects.filter(slug=request.POST.get('house_type')).first()
        listing.bedrooms = int(request.POST.get('bedrooms', 1))
        listing.bathrooms = int(request.POST.get('bathrooms', 1))
        listing.rent = request.POST.get('rent')
        listing.contact_name = request.POST.get('contact_name', '')
        listing.contact_phone = request.POST.get('contact_phone', '')
        listing.status = request.POST.get('status', 'available')
        if request.FILES.get('image'):
            listing.image = request.FILES['image']
        extra_images = request.FILES.getlist('extra_images')
        if extra_images:
            start = listing.images.count()
            for i, img in enumerate(extra_images):
                listing.images.create(image=img, order=start + i)
        listing.save()
        messages.success(request, 'Listing updated.')
        return redirect('accounts:admin_listings')
    from core.models import HouseType
    return render(request, 'accounts/admin_listing_form.html', {'listing': listing, 'title': 'Edit Listing', 'house_types': HouseType.objects.all()})


@login_required
def admin_listing_delete(request, pk):
    if request.user.profile.role != 'admin':
        return redirect('website:home')
    from website.models import AdminListing
    listing = get_object_or_404(AdminListing, pk=pk)
    listing.delete()
    messages.success(request, 'Listing deleted.')
    return redirect('accounts:admin_listings')


@login_required
def admin_landlord_detail(request, landlord_id):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Admin access required.')
        return redirect('website:home')
    landlord = get_object_or_404(User, pk=landlord_id, profile__role='landlord')
    subs = LandlordSubscription.objects.filter(landlord=landlord).select_related('plan').order_by('-created_at')
    unit_count = Unit.objects.filter(property__owner=landlord).count()
    fee = get_fee_per_unit(landlord)
    monthly_fee = unit_count * fee
    trial_info = landlord_trial_info(landlord)
    return render(request, 'accounts/admin_landlord_detail.html', {
        'landlord': landlord, 'subscriptions': subs,
        'unit_count': unit_count, 'fee': fee, 'monthly_fee': monthly_fee,
        'trial_info': trial_info, 'active_tab': 'landlords',
    })



