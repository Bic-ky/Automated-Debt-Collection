from datetime import date
from django import forms
from .models import Client,Action,Bill

from django.utils import timezone


class ExcelUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'dropify'}))

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'
        widgets = {
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.TextInput(attrs={'class': 'form-control'}),
            'collector': forms.Select(attrs={'class': 'form-control'}),
            'guarantee_world_insurer': forms.TextInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class ActionUpdateForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ['completed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add form control class to the completed field
        self.fields['completed'].widget.attrs.update({'class': 'form-control'})

    

from django import forms

class ActionCreationForm(forms.ModelForm):
    class Meta:
        model = Action
        exclude = ['action_amount']  # Exclude action_amount from form fields

    action_date = forms.DateField(initial=timezone.now(), widget=forms.DateInput(attrs={'readonly': 'readonly'}))

    action_type = forms.ChoiceField(
        choices=Action.ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn btn-primary waves-effect waves-light'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bill_no'].queryset = Bill.objects.none()

        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
                self.fields['bill_no'].queryset = Bill.objects.filter(short_name_id=client_id).order_by('bill_no')
            except (ValueError, TypeError):
                pass  # Invalid input from the client; ignore and fallback to an empty queryset
        elif self.instance.pk:
            self.fields['bill_no'].queryset = self.instance.short_name.bill_set.order_by('bill_no')

        # Add form control to other fields if needed
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


