from django import forms
from .models import User , UserProfile
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import PasswordChangeForm

from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-inline'})
    )

    class Meta:
        model = User
        fields = ('phone_number', 'password', 'role')

     