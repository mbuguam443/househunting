from django import forms
from .models import Tenancy, RentPayment, MaintenanceRequest
from units.models import Unit

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
        fields = ['amount', 'due_date', 'paid_date', 'reference', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'paid_date': forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}),
            'amount': forms.NumberInput(attrs={'class': 'oinp'}),
            'reference': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'M-Pesa ref'}),
            'notes': forms.Textarea(attrs={'class': 'oinp', 'rows': 3}),
        }

class MarkPaidForm(forms.Form):
    paid_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'oinp'}))
    reference = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'M-Pesa reference'}))
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
