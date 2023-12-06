from django.contrib import admin
from .models import Client
from import_export.admin import ImportExportActionModelAdmin

@admin.register(Client)
class clientData(ImportExportActionModelAdmin):
    list_display = ['account_name', 'short_name', 'balance', 'phone_number', 'collector']
    list_editable = ['collector']  # Add 'collector' to make it editable directly from the list view
