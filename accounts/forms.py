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
        fields = ['phone', 'avatar', 'mpesa_consumer_key', 'mpesa_consumer_secret', 'mpesa_passkey', 'mpesa_shortcode', 'mpesa_callback_url']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'oinp'}),
            'avatar': forms.FileInput(attrs={'class': 'oinp'}),
            'mpesa_consumer_key': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Your Daraja Consumer Key'}),
            'mpesa_consumer_secret': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Your Daraja Consumer Secret'}),
            'mpesa_passkey': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'Your M-Pesa Passkey'}),
            'mpesa_shortcode': forms.TextInput(attrs={'class': 'oinp', 'placeholder': 'e.g. 174379'}),
            'mpesa_callback_url': forms.URLInput(attrs={'class': 'oinp', 'placeholder': 'https://your-ngrok-url.ngrok-free.app'}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {f: forms.TextInput(attrs={'class': 'oinp'}) for f in fields}
