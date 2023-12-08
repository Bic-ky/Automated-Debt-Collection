from django.contrib import admin
from .models import Client, Bill
from import_export.admin import ImportExportActionModelAdmin

@admin.register(Client)
class ClientData(ImportExportActionModelAdmin):
    list_display = ['short_name', 'account_name', 'balance', 'phone_number', 'collector']
    list_editable = ['collector']  # Add 'collector' to make it editable directly from the list view
    search_fields = ['short_name', 'account_name', 'phone_number']

@admin.register(Bill)
class BillData(ImportExportActionModelAdmin):
    list_display = ['short_name', 'type', 'bill_no', 'inv_amount', 'due_date']
    search_fields = ['short_name', 'bill_no']
   