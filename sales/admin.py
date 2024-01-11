from django.contrib import admin
from .models import Client, Bill,Action,DailyBalance
from import_export.admin import ImportExportActionModelAdmin

@admin.register(Client)
class ClientData(ImportExportActionModelAdmin):
    list_display = ['short_name', 'account_name', 'balance', 'phone_number', 'collector']
    list_editable = ['collector']  
    search_fields = ['short_name', 'account_name']

@admin.register(Bill)
class BillData(ImportExportActionModelAdmin):
    list_display = ['short_name', 'type', 'bill_no', 'inv_amount', 'due_date','balance',]
    search_fields = ['short_name__account_name', 'bill_no'] 
   

@admin.register(Action)
class ActionData(ImportExportActionModelAdmin):
    list_display = ['action_date','short_name', 'action_type','type','completed','subtype','followup_date']
    search_fields = ['type']
    list_editable = ['completed','type','action_type']  
    
@admin.register(DailyBalance)
class BalanceData(ImportExportActionModelAdmin):
    list_display = ['collector', 'total_balance', 'date',]
    
    
