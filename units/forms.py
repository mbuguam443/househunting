from django import forms
from .models import Unit, UnitAmenity

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['property', 'unit_number', 'house_type', 'bedrooms', 'bathrooms',
                   'monthly_rent', 'deposit', 'floor', 'description', 'status',
                   'available_from', 'image', 'image_2', 'image_3']
        widgets = {
            'unit_number': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'e.g. A12'}),
            'house_type': forms.Select(attrs={'class': 'oinp'}),
            'bedrooms': forms.NumberInput(attrs={'class': 'oinp'}),
            'bathrooms': forms.NumberInput(attrs={'class': 'oinp'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'oinp', 'placeholder': 'KES'}),
            'deposit': forms.NumberInput(attrs={'class': 'oinp', 'placeholder': 'KES'}),
            'floor': forms.NumberInput(attrs={'class': 'oinp'}),
            'description': forms.Textarea(attrs={'class': 'oinp', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'oinp'}),
            'available_from': forms.DateInput(attrs={'class': 'oinp', 'type': 'date'}),
            'image': forms.FileInput(attrs={'class': 'oinp'}),
            'image_2': forms.FileInput(attrs={'class': 'oinp'}),
            'image_3': forms.FileInput(attrs={'class': 'oinp'}),
            'property': forms.Select(attrs={'class': 'oinp'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['property'].queryset = user.properties.all()

class UnitAmenityForm(forms.ModelForm):
    class Meta:
        model = UnitAmenity
        fields = ['water', 'electricity', 'parking', 'security', 'internet', 'furnished']
        widgets = {f: forms.CheckboxInput(attrs={'class': 'form-check-input'}) for f in fields}
