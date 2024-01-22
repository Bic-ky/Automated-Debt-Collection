from django import forms
from .models import User
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



class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add form control attributes to the fields
        self.fields['old_password'].widget = forms.PasswordInput(attrs={'class': 'form-control'})
        self.fields['new_password1'].widget = forms.PasswordInput(attrs={'class': 'form-control'})
        self.fields['new_password2'].widget = forms.PasswordInput(attrs={'class': 'form-control'})