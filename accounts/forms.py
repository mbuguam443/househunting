from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'oinp'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'oinp')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'avatar', 'mpesa_consumer_key', 'mpesa_consumer_secret', 'mpesa_passkey', 'mpesa_shortcode', 'c2b_shortcode', 'mpesa_callback_url', 'c2b_confirmation_url', 'c2b_validation_url', 'b2c_initiator_name', 'b2c_initiator_password']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'oinp'}),
            'avatar': forms.FileInput(attrs={'class': 'oinp'}),
            'mpesa_consumer_key': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Your Daraja Consumer Key'}),
            'mpesa_consumer_secret': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Your Daraja Consumer Secret'}),
            'mpesa_passkey': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Your M-Pesa Passkey'}),
            'mpesa_shortcode': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'e.g. 174379 (STK Push)'}),
            'c2b_shortcode': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'e.g. 654321 (C2B Paybill)'}),
            'mpesa_callback_url': forms.URLInput(attrs={'class': 'oinp', 'placeholder': 'https://your-ngrok-url.ngrok-free.app'}),
            'c2b_confirmation_url': forms.URLInput(attrs={'class': 'oinp', 'placeholder': 'https://abc123.ngrok.io/c2b/confirmation/'}),
            'c2b_validation_url': forms.URLInput(attrs={'class': 'oinp', 'placeholder': 'https://abc123.ngrok.io/c2b/validation/'}),
            'b2c_initiator_name': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'B2C initiator username'}),
            'b2c_initiator_password': forms.PasswordInput(attrs={'class': 'oinp', 'placeholder': 'B2C initiator password'}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {f: forms.TextInput(attrs={'class': 'oinp'}) for f in fields}
