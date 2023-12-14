from django.contrib import admin
from .models import Client, Bill,Action
from import_export.admin import ImportExportActionModelAdmin

@admin.register(Client)
class ClientData(ImportExportActionModelAdmin):
    list_display = ['short_name', 'account_name', 'balance', 'phone_number', 'collector']
    list_editable = ['collector']  
    search_fields = ['short_name', 'account_name']

@admin.register(Bill)
class BillData(ImportExportActionModelAdmin):
    list_display = ['short_name', 'type', 'bill_no', 'inv_amount', 'due_date']
    search_fields = ['short_name__account_name', 'bill_no'] 
   
@admin.register(Action)
class ActionData(ImportExportActionModelAdmin):
    list_display = ['action_date', 'action_type','type', 'action_amount', 'short_name']
    search_fields = ['short_name__account_name', 'type']
