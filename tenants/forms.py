from django import forms
from django.contrib.auth.models import User
from .models import Tenancy, RentPayment, MaintenanceRequest, LeaseAgreement, UtilityBill
from units.models import Unit
from properties.models import Property


class TenantRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'oinp')
        self.fields['email'].required = True
        self.fields['email'].widget.attrs['placeholder'] = 'e.g. tenant@example.com'
        self.fields['username'].widget.attrs['placeholder'] = 'Username for tenant portal login'

class TenancyForm(forms.ModelForm):
    class Meta:
        model = Tenancy
        fields = ['tenant', 'unit', 'start_date', 'monthly_rent', 'deposit_paid']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'oinp', 'readonly': True}),
            'deposit_paid': forms.NumberInput(attrs={'class': 'oinp', 'readonly': True}),
        }

    def __init__(self, *args, **kwargs):
        landlord = kwargs.pop('landlord')
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        self.fields['tenant'].queryset = User.objects.filter(profile__role='tenant').order_by('username')
        self.fields['tenant'].widget.attrs.update({'class': 'oinp'})
        self.fields['unit'].queryset = Unit.objects.filter(property__owner=landlord, status='vacant').select_related('property')
        self.fields['unit'].widget.attrs.update({'class': 'oinp'})
        self.fields['unit'].label_from_instance = lambda obj: f'{obj.property.name} - {obj.unit_number} ({obj.house_type.name}, KES {obj.monthly_rent})'
        self.fields['monthly_rent'].required = False
        self.fields['deposit_paid'].required = False

class RentPaymentForm(forms.ModelForm):
    class Meta:
        model = RentPayment
        fields = ['amount', 'due_date', 'paid_date', 'payment_method', 'reference', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'paid_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'amount': forms.NumberInput(attrs={'class': 'oinp'}),
            'payment_method': forms.Select(attrs={'class': 'oinp'}),
            'reference': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'M-Pesa confirmation code'}),
            'notes': forms.Textarea(attrs={'class': 'oinp', 'rows': 3}),
        }

class MarkPaidForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01'}))
    paid_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}))
    payment_method = forms.ChoiceField(choices=RentPayment.METHOD_CHOICES, widget=forms.Select(attrs={'class': 'oinp'}))
    reference = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Transaction ref or receipt no.'}))
    notes = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'class': 'oinp', 'rows': 2}))

class RecordPaymentForm(forms.Form):
    tenancy = forms.ModelChoiceField(
        queryset=Tenancy.objects.none(),
        widget=forms.Select(attrs={'class': 'oinp'}),
        label='Tenant / Unit',
    )
    amount = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01', 'placeholder': 'Amount paid'}))
    paid_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}))
    payment_method = forms.ChoiceField(choices=RentPayment.METHOD_CHOICES, widget=forms.Select(attrs={'class': 'oinp'}))
    reference = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Receipt or ref number'}))
    notes = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'class': 'oinp', 'rows': 2, 'placeholder': 'Optional notes'}))

    def __init__(self, *args, landlord=None, **kwargs):
        super().__init__(*args, **kwargs)
        if landlord:
            self.fields['tenancy'].queryset = Tenancy.objects.filter(
                unit__property__owner=landlord, status='active'
            ).select_related('tenant', 'unit').order_by('tenant__username')
            self.fields['tenancy'].label_from_instance = lambda obj: f'{obj.tenant.username} @ {obj.unit.unit_number} ({obj.unit.property.name}) - KES {obj.monthly_rent}/mo'

class UtilityBillForm(forms.ModelForm):
    tenancy = forms.ModelChoiceField(
        queryset=Tenancy.objects.none(),
        widget=forms.Select(attrs={'class': 'oinp', 'style': 'max-width:400px'}),
        label='Tenant / Unit',
        required=False,
    )
    property = forms.ModelChoiceField(
        queryset=Property.objects.none(),
        widget=forms.Select(attrs={'class': 'oinp', 'style': 'max-width:400px'}),
        label='Property (for billing all tenants)',
        required=False,
    )
    bill_all = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'oinp', 'style': 'width:18px;height:18px;accent-color:#6a4cdb'}),
        label='Apply to all active tenants in this property',
        required=False,
    )

    class Meta:
        model = UtilityBill
        fields = ['utility_type', 'amount', 'period_start', 'period_end', 'due_date', 'units_consumed', 'rate_per_unit', 'notes']
        widgets = {
            'utility_type': forms.Select(attrs={'class': 'oinp'}),
            'amount': forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01', 'placeholder': 'Total bill amount'}),
            'period_start': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'period_end': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'units_consumed': forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01', 'placeholder': 'Optional — for tenant reference'}),
            'rate_per_unit': forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01', 'placeholder': 'Optional — for tenant reference'}),
            'notes': forms.Textarea(attrs={'class': 'oinp', 'rows': 3, 'placeholder': 'Optional notes'}),
        }

    def __init__(self, *args, landlord=None, **kwargs):
        if 'landlord' not in kwargs and len(args) >= 1:
            landlord = args[0]
            args = args[1:]
        super().__init__(*args, **kwargs)
        self.fields['units_consumed'].required = False
        self.fields['rate_per_unit'].required = False
        if landlord:
            self.fields['tenancy'].queryset = Tenancy.objects.filter(
                unit__property__owner=landlord, status='active'
            ).select_related('tenant', 'unit').order_by('tenant__username')
            self.fields['tenancy'].label_from_instance = lambda obj: f'{obj.tenant.username} @ {obj.unit.unit_number} ({obj.unit.property.name}) - KES {obj.monthly_rent}/mo'
            self.fields['property'].queryset = Property.objects.filter(owner=landlord).order_by('name')

    def clean(self):
        cleaned = super().clean()
        tenancy = cleaned.get('tenancy')
        bill_all = cleaned.get('bill_all')
        prop = cleaned.get('property')
        if not tenancy and not (bill_all and prop):
            raise forms.ValidationError('Select a tenant/unit or check "Apply to all" and select a property.')
        if not cleaned.get('amount'):
            raise forms.ValidationError('Enter the bill amount.')
        return cleaned

class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['title', 'description', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'e.g. Leaking tap'}),
            'description': forms.Textarea(attrs={'class': 'oinp', 'rows': 4, 'placeholder': 'Describe the issue in detail'}),
            'priority': forms.Select(attrs={'class': 'oinp'}),
        }

class MaintenanceStatusForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['status', 'landlord_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'oinp'}),
            'landlord_notes': forms.Textarea(attrs={'class': 'oinp', 'rows': 3, 'placeholder': 'Notes for the tenant'}),
        }

class LeaseForm(forms.ModelForm):
    class Meta:
        model = LeaseAgreement
        fields = ['start_date', 'end_date', 'monthly_rent', 'deposit_amount', 'payment_due_day', 'late_fee', 'notice_period_days', 'terms']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01'}),
            'payment_due_day': forms.NumberInput(attrs={'class': 'oinp', 'min': 1, 'max': 28}),
            'late_fee': forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01'}),
            'notice_period_days': forms.NumberInput(attrs={'class': 'oinp'}),
            'terms': forms.Textarea(attrs={'class': 'oinp', 'rows': 6, 'placeholder': 'General terms and conditions of the lease agreement...'}),
        }
