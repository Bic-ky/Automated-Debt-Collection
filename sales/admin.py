from django.contrib import admin
from .models import Client,Bill
from import_export.admin import ImportExportActionModelAdmin

@admin.register(Client)
class clientData(ImportExportActionModelAdmin):
    list_display = ['short_name','account_name',  'balance', 'phone_number', 'collector']
    list_editable = ['collector']  # Add 'collector' to make it editable directly from the list view
@admin.register(Bill)
class billData(ImportExportActionModelAdmin):
    list_display = ['short_name', 'type', 'bill_no', 'inv_amount','due_date']


   