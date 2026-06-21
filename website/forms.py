from django import forms
from .models import Inquiry

class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Your name'}),
            'email': forms.EmailInput(attrs={'class': 'oinp', 'placeholder': 'your@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'oinp', 'placeholder': '+254 7XX XXX XXX'}),
            'message': forms.Textarea(attrs={'class': 'oinp', 'rows': 4, 'placeholder': 'I am interested in this unit...'}),
        }
