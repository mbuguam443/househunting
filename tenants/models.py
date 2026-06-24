from django.db import models
from django.conf import settings
from units.models import Unit

class Tenancy(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('terminated', 'Terminated'),
    ]
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tenancies')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='tenancies')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    deposit_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'tenancies'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.tenant.username} @ {self.unit.unit_number} ({self.get_status_display()})'

class RentPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('late', 'Late'),
    ]
    METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('other', 'Other'),
    ]
    tenancy = models.ForeignKey(Tenancy, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='mpesa')
    reference = models.CharField(max_length=100, blank=True, help_text='Transaction reference (M-Pesa code or receipt)')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f'{self.tenancy.tenant.username} - KES {self.amount} ({self.get_status_display()})'

class MpesaTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    payment = models.ForeignKey(RentPayment, on_delete=models.CASCADE, related_name='mpesa_transactions')
    phone = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True)
    response_code = models.CharField(max_length=10, blank=True)
    response_description = models.CharField(max_length=255, blank=True)
    receipt = models.CharField(max_length=50, blank=True, help_text='M-Pesa receipt number')
    transaction_date = models.DateTimeField(null=True, blank=True)
    result_code = models.CharField(max_length=10, blank=True)
    result_desc = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    raw_callback = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.phone} - KES {self.amount} ({self.get_status_display()})'

class LeaseAgreement(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('terminated', 'Terminated'),
        ('expired', 'Expired'),
    ]
    tenancy = models.OneToOneField(Tenancy, on_delete=models.CASCADE, related_name='lease')
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_due_day = models.IntegerField(default=5)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notice_period_days = models.IntegerField(default=30)
    terms = models.TextField(blank=True)
    clauses = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    landlord_accepted = models.BooleanField(default=False)
    landlord_accepted_at = models.DateTimeField(null=True, blank=True)
    tenant_accepted = models.BooleanField(default=False)
    tenant_accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Lease: {self.tenancy.tenant.username} @ {self.tenancy.unit.unit_number}'


class MaintenanceRequest(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='maintenance_requests')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='maintenance_requests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    landlord_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.tenant.username}'
