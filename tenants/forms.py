from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Tenancy, RentPayment, MaintenanceRequest
from units.models import Unit


class TenantRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'oinp')
        self.fields['email'].required = True
        self.fields['email'].widget.attrs['placeholder'] = 'e.g. tenant@example.com'
        self.fields['username'].widget.attrs['placeholder'] = 'Username for tenant portal login'
        self.fields['password1'].widget.attrs['placeholder'] = 'At least 8 characters'
        self.fields['password2'].widget.attrs['placeholder'] = 'Repeat the password'

class TenancyForm(forms.ModelForm):
    class Meta:
        model = Tenancy
        fields = ['tenant', 'unit', 'start_date', 'monthly_rent', 'deposit_paid']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'oinp', 'placeholder': 'Monthly rent in KES'}),
            'deposit_paid': forms.NumberInput(attrs={'class': 'oinp', 'placeholder': 'Deposit amount'}),
        }

    def __init__(self, *args, **kwargs):
        landlord = kwargs.pop('landlord')
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        self.fields['tenant'].queryset = User.objects.filter(profile__role='tenant').order_by('username')
        self.fields['tenant'].widget.attrs.update({'class': 'oinp'})
        self.fields['unit'].queryset = Unit.objects.filter(property__owner=landlord, status='vacant').select_related('property')
        self.fields['unit'].widget.attrs.update({'class': 'oinp'})
        self.fields['unit'].label_from_instance = lambda obj: f'{obj.property.name} - {obj.unit_number} ({obj.get_house_type_display()}, KES {obj.monthly_rent})'

class RentPaymentForm(forms.ModelForm):
    class Meta:
        model = RentPayment
        fields = ['amount', 'due_date', 'paid_date', 'payment_method', 'reference', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'paid_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'amount': forms.NumberInput(attrs={'class': 'oinp'}),
            'payment_method': forms.Select(attrs={'class': 'oinp'}),
            'reference': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Transaction ref (M-Pesa code or receipt)'}),
            'notes': forms.Textarea(attrs={'class': 'oinp', 'rows': 3}),
        }

class MarkPaidForm(forms.Form):
    paid_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}))
    payment_method = forms.ChoiceField(choices=RentPayment.METHOD_CHOICES, widget=forms.Select(attrs={'class': 'oinp'}))
    reference = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'M-Pesa code, receipt no., or leave blank for cash'}))
    notes = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'class': 'oinp', 'rows': 2}))

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
