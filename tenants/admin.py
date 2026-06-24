from django.contrib import admin
from .models import Tenancy, RentPayment, MaintenanceRequest, LeaseAgreement

@admin.register(Tenancy)
class TenancyAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'unit', 'status', 'start_date', 'end_date', 'monthly_rent']
    list_filter = ['status']
    search_fields = ['tenant__username', 'unit__unit_number']

@admin.register(RentPayment)
class RentPaymentAdmin(admin.ModelAdmin):
    list_display = ['tenancy', 'amount', 'due_date', 'paid_date', 'status']
    list_filter = ['status']

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'tenant', 'unit', 'priority', 'status']
    list_filter = ['priority', 'status']

@admin.register(LeaseAgreement)
class LeaseAgreementAdmin(admin.ModelAdmin):
    list_display = ['tenancy', 'status', 'start_date', 'end_date', 'monthly_rent']
    list_filter = ['status']