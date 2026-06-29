from django import forms
from .models import Property

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'description', 'county', 'town', 'estate', 'address', 'latitude', 'longitude', 'image', 'water_rate', 'electricity_rate', 'trash_rate']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'e.g. Green Valley Apartments'}),
            'description': forms.Textarea(attrs={'class': 'oinp', 'rows': 4, 'placeholder': 'Describe the property...'}),
            'county': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'e.g. Nairobi'}),
            'town': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'e.g. Kilimani'}),
            'estate': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'e.g. Woodley Estate'}),
            'address': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Street / building name'}),
            'latitude': forms.NumberInput(attrs={'class': 'oinp', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'oinp', 'step': 'any'}),
            'image': forms.FileInput(attrs={'class': 'oinp'}),
            'water_rate': forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01', 'placeholder': 'e.g. 100.00'}),
            'electricity_rate': forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01', 'placeholder': 'e.g. 50.00'}),
            'trash_rate': forms.NumberInput(attrs={'class': 'oinp', 'step': '0.01', 'placeholder': 'e.g. 200.00'}),
        }
