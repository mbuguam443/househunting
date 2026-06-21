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
        fields = ['phone', 'avatar']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'oinp'}),
            'avatar': forms.FileInput(attrs={'class': 'oinp'}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {f: forms.TextInput(attrs={'class': 'oinp'}) for f in fields}
