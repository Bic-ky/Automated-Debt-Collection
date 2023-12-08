# forms.py
from django import forms

class ExcelUploadForm(forms.Form):
    file = forms.FileField()

    # Fields for Client model
    account_name = forms.CharField(max_length=255, required=False)
    short_name = forms.CharField(max_length=255, required=False)
    address = forms.CharField(max_length=255, required=False)
    # Add other fields for the Client model

    # Fields for Bill model
    type = forms.CharField(max_length=40, required=False)
    bill_no = forms.CharField(max_length=40, required=False)
    date = forms.DateField(required=False)
    due_date = forms.DateField(required=False)
    days = forms.IntegerField(required=False)
    inv_amount = forms.FloatField(required=False)
    cycle1 = forms.FloatField(required=False)
    cycle2 = forms.FloatField(required=False)
    cycle3 = forms.FloatField(required=False)
    cycle4 = forms.FloatField(required=False)
    cycle5 = forms.FloatField(required=False)
    cycle6 = forms.FloatField(required=False)
    cycle7 = forms.FloatField(required=False)
    cycle8 = forms.FloatField(required=False)
    cycle9 = forms.FloatField(required=False)
    balance = forms.FloatField(required=False)
