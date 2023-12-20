from datetime import timezone
from django import forms
from .models import Client,Action,Bill

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
        self.fields['completed'].widget.attrs.update({'class': 'form-control'})
        

class AddActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ['action_date', 'action_type', 'client', 'bill_no', 'action_amount', 'completed']

    action_date = forms.DateField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    action_type = forms.ChoiceField(choices=Action.ACTION_CHOICES, widget=forms.RadioSelect)
    client = forms.ModelChoiceField(queryset=Client.objects.all(), widget=forms.Select(attrs={'class': 'form-control', 'data-toggle': 'select2'}))
    bill_no = forms.ModelChoiceField(queryset=Bill.objects.none(), widget=forms.Select(attrs={'class': 'form-control', 'data-toggle': 'select2', 'disabled': 'disabled'}))
    action_amount = forms.FloatField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    completed = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'mt-3', 'data-toggle': 'switchery', 'data-color': '#4BB543', 'data-size': 'small'}))