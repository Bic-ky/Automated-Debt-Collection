# filters.py
import django_filters
from django import forms
from django_filters.widgets import RangeWidget

from account.models import User
from .models import Action, Client

class ActionFilter(django_filters.FilterSet):
    short_name__collector = django_filters.ModelChoiceFilter(
        queryset=User.objects.filter(role=User.USER),
        empty_label='Select Collector ',
        label='',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
    action_date = django_filters.DateFromToRangeFilter(
        widget=RangeWidget(attrs={'class': 'form-control', 'placeholder': 'Date Filter'}),
    )

    # completed = django_filters.BooleanFilter(
    #     label='Completed',
    #     widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    # )


    short_name = django_filters.ModelChoiceFilter(
        queryset=Client.objects.all(),
        empty_label='Select Client Name',
        label='',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Action
        fields = ['short_name__collector', 'action_date', 'short_name', 'completed']
