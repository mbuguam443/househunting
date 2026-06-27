from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta


class PlatformConfig(models.Model):
    fee_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=50.00,
        help_text='Monthly platform fee per unit (KES)')
    trial_days = models.PositiveIntegerField(default=14, help_text='Free trial duration in days')
    callback_url = models.CharField(max_length=500, blank=True, help_text='Override M-Pesa callback URL (e.g., ngrok URL). Leave blank to use MPESA_CALLBACK_URL from settings.')
    c2b_confirmation_url = models.CharField(max_length=500, blank=True, help_text='C2B Confirmation URL (public URL M-Pesa will call). Falls back to domain + /mpesa/c2b/confirmation/')
    c2b_validation_url = models.CharField(max_length=500, blank=True, help_text='C2B Validation URL (public URL M-Pesa will call). Falls back to domain + /mpesa/c2b/validation/')
    c2b_registered = models.BooleanField(default=False, help_text='Whether C2B URLs have been registered with Safaricom')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Platform Configuration'

    def __str__(self):
        return f'KES {self.fee_per_unit}/unit'


class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('landlord', 'Landlord'),
        ('tenant', 'Tenant'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='landlord')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    fee_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=50.00,
        help_text='Monthly platform fee per unit for this landlord (KES). Set 0 for free.')
    trial_started_at = models.DateTimeField(null=True, blank=True, help_text='When the free trial started')
    mpesa_consumer_key = models.CharField(max_length=200, blank=True, help_text='Your M-Pesa Consumer Key (Daraja API)')
    mpesa_consumer_secret = models.CharField(max_length=200, blank=True, help_text='Your M-Pesa Consumer Secret')
    mpesa_passkey = models.CharField(max_length=200, blank=True, help_text='Your M-Pesa Passkey')
    mpesa_shortcode = models.CharField(max_length=20, blank=True, help_text='Your M-Pesa Shortcode / Paybill (for STK Push)')
    c2b_shortcode = models.CharField(max_length=20, blank=True, help_text='Your C2B Paybill number (for receiving M-Pesa payments). Different from STK Push shortcode.')
    mpesa_callback_url = models.CharField(max_length=500, blank=True, help_text='Override M-Pesa callback URL (e.g., ngrok URL) for this landlord')
    c2b_confirmation_url = models.CharField(max_length=500, blank=True, help_text='C2B Confirmation URL (public URL M-Pesa will call). Leave blank to auto-derive.')
    c2b_validation_url = models.CharField(max_length=500, blank=True, help_text='C2B Validation URL (public URL M-Pesa will call). Leave blank to auto-derive.')
    c2b_registered = models.BooleanField(default=False, help_text='Whether C2B URLs are registered for this landlord')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(help_text='Number of days the subscription lasts')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['amount']

    def __str__(self):
        return f'{self.name} — KES {self.amount}'


class LandlordSubscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    landlord = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='subscriptions')
    unit_count = models.PositiveIntegerField(default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text='Total fee = unit_count × fee_per_unit at time of creation')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    payment_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.landlord.username} — KES {self.amount} ({self.get_status_display()})'


def require_landlord_sub(user):
    """Check if landlord has active subscription. Returns (has_active, response_or_None)."""
    from django.shortcuts import redirect as redir
    if user.profile.role == 'landlord' and not landlord_has_active_sub(user):
        return False, redir('dashboard:overview')
    return True, None


def get_trial_end(user):
    """Returns the trial end date for a landlord, or None if not applicable."""
    if user.profile.role != 'landlord':
        return None
    if user.profile.fee_per_unit is not None and user.profile.fee_per_unit == 0:
        return None
    if not user.profile.trial_started_at:
        return None
    cfg, _ = PlatformConfig.objects.get_or_create(pk=1, defaults={'fee_per_unit': 50.00, 'trial_days': 14})
    return user.profile.trial_started_at.date() + timedelta(days=cfg.trial_days)


def landlord_has_active_sub(user):
    if user.profile.role != 'landlord':
        return True
    # Zero fee = free service, no subscription needed
    if user.profile.fee_per_unit is not None and user.profile.fee_per_unit == 0:
        return True
    # Active subscription
    sub = user.subscriptions.filter(status='active', end_date__gte=date.today()).first()
    if sub:
        return True
    # Free trial period
    trial_end = get_trial_end(user)
    if trial_end and trial_end >= date.today():
        return True
    return False


def landlord_trial_info(user):
    """Returns dict with trial days remaining and warning thresholds, or None."""
    if user.profile.role != 'landlord':
        return None
    if user.profile.fee_per_unit is not None and user.profile.fee_per_unit == 0:
        return None
    if not user.profile.trial_started_at:
        return None
    trial_end = get_trial_end(user)
    if not trial_end:
        return None
    today = date.today()
    remaining = (trial_end - today).days
    if remaining < 0:
        return None
    cfg, _ = PlatformConfig.objects.get_or_create(pk=1, defaults={'fee_per_unit': 50.00, 'trial_days': 14})
    return {
        'end_date': trial_end,
        'remaining_days': remaining,
        'total_days': cfg.trial_days,
        'is_expiring': remaining <= 7,
    }


def get_fee_per_unit(landlord=None):
    if landlord and hasattr(landlord, 'profile') and landlord.profile.fee_per_unit is not None:
        return landlord.profile.fee_per_unit
    cfg, _ = PlatformConfig.objects.get_or_create(pk=1, defaults={'fee_per_unit': 50.00})
    return cfg.fee_per_unit


def landlord_subscription_status(user):
    sub = LandlordSubscription.objects.filter(landlord=user).first()
    if not sub:
        return 'none', None
    if sub.status == 'active' and sub.end_date >= date.today():
        return 'active', sub
    if sub.status == 'active' and sub.end_date < date.today():
        sub.status = 'expired'
        sub.save()
        return 'expired', sub
    return sub.status, sub
