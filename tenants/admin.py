from django.contrib import admin
from .models import Tenancy, RentPayment, MaintenanceRequest, LeaseAgreement, C2BTransaction, MpesaTransaction, UtilityBill, B2CTransaction

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

@admin.register(C2BTransaction)
class C2BTransactionAdmin(admin.ModelAdmin):
    list_display = ['trans_id', 'amount', 'phone', 'bill_ref', 'matched_tenant', 'created_at']
    search_fields = ['bill_ref', 'trans_id', 'phone', 'first_name', 'last_name']
    list_filter = ['created_at']

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['phone', 'amount', 'receipt', 'status', 'payment', 'created_at']
    search_fields = ['receipt', 'phone', 'checkout_request_id']
    list_filter = ['status', 'created_at']

@admin.register(UtilityBill)
class UtilityBillAdmin(admin.ModelAdmin):
    list_display = ['utility_type', 'tenancy', 'amount', 'period_start', 'period_end', 'due_date', 'status']
    list_filter = ['utility_type', 'status']
    search_fields = ['tenancy__tenant__username', 'tenancy__unit__unit_number']

@admin.register(B2CTransaction)
class B2CTransactionAdmin(admin.ModelAdmin):
    list_display = ['landlord', 'amount', 'recipient_phone', 'transaction_receipt', 'status', 'result_code', 'created_at']
    list_filter = ['status', 'result_code']
    search_fields = ['transaction_receipt', 'transaction_id', 'conversation_id', 'landlord__username']