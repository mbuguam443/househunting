from django.db import models
from django.contrib.auth.models import User
from datetime import date


class PlatformConfig(models.Model):
    fee_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=50.00,
        help_text='Monthly platform fee per unit (KES)')
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


def landlord_has_active_sub(user):
    if user.profile.role != 'landlord':
        return True
    # Zero fee = free service, no subscription needed
    if user.profile.fee_per_unit is not None and user.profile.fee_per_unit == 0:
        return True
    sub = user.subscriptions.filter(status='active', end_date__gte=date.today()).first()
    return sub is not None


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
