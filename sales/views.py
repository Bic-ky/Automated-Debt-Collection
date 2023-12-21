from django.forms import ValidationError
from datetime import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from . models import Client,Bill,Action
from .resources import BillResource
from django.contrib import messages
from .forms import ExcelUploadForm  
from django.core.exceptions import ValidationError
import pandas as pd
from IPython.display import FileLink
from django.http import FileResponse, HttpResponse
from django.core.files.storage import default_storage
from pandas.errors import EmptyDataError
from nepali_date_converter import english_to_nepali_converter, nepali_to_english_converter
from django.db.models import Sum,F
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from .models import Client
from .forms import ClientForm
from .forms import ActionUpdateForm,ActionCreationForm
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from .models import Client, Bill
from datetime import date
# Create your views here.

def profile(request):
    return render(request , 'profile.html')

def convert_date_format(input_date):
    try:
        # Check if the input_date is already a datetime object
        if isinstance(input_date, datetime):
            # If it is, return the formatted date as a string
            return input_date.strftime('%Y/%m/%d')
        
        # If not, parse the input string and format it
        input_datetime = datetime.strptime(str(input_date), '%Y-%m-%d %H:%M:%S')
        output_date = input_datetime.strftime('%Y/%m/%d')
        
        return output_date
    except ValueError:
        # If parsing fails, assume the input is already in the desired format
        return input_date

def convert_nepali_to_ad(nepali_date):
    try:
        # Parse the Nepali date into year, month, and day
        nepali_year, nepali_month, nepali_day = map(int, nepali_date.split('/'))

        # Convert Nepali date to English date
        english_date = nepali_to_english_converter(nepali_year, nepali_month, nepali_day)
        return english_date
    except Exception as e:
        print(f"Error converting Nepali date: {e}")
        return None  # or return the original value if conversion fails

def upload_excel(request):
    success_messages = []
    error_messages = []
    download_link = None  # Initialize download_link

    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                excel_data = pd.read_excel(request.FILES['file'])
                
                # Skip the first 3 rows
                df = excel_data.iloc[3:]
                
                # Set the 0th row data as column headings
                df.columns = df.iloc[0]
                
                # Check if the expected columns are present
                expected_columns = ['Type', 'Bill No.', 'Date', 'Due Date', 'Days', 'Inv.Amt', '0 - 15',
                                    '16 - 30', '31 - 45', '46 - 60', '61 - 75', '76 - 90', '91 - 105',
                                    '106 - 120', 'Over 121', 'Balance']

                if not all(col in df.columns for col in expected_columns):
                    error_message = 'Wrong format file. Please make sure all required columns are present.'
                    error_messages.append(error_message)
                    print(error_messages)  
                    return render(request, 'upload.html', {'form': form, 'error_message': error_message})
                
                # Replace "Type" column with "1" where "Bill No." contains "Ledger =>"
                df.loc[df['Bill No.'].str.contains('Ledger =>', na=False), 'Type'] = '1'

                # Remove rows where 'Type' is '1'
                df = df[df['Type'] != '1']

                # Reset the index after filtering
                df = df.reset_index(drop=True)

                # Reset the index after removing rows and set the 0th row as the new column headings
                df = df.iloc[1:].reset_index(drop=True)
                df.fillna(0, inplace=True)

                # Define a list of values to check for in the "Type" column
                values_to_check = ['0', 'SB', 'OB']

                # Initialize a variable to store the first 'Bill No.' value
                first_bill_no = None

                # Iterate through the DataFrame
                for index, row in df.iterrows():
                    type_value = str(row['Type']).strip()
                    
                    # Check if the 'Type' value is '0'
                    if type_value == '0':
                        # Reset the first_bill_no when '0' is encountered
                        first_bill_no = None
                    
                    # If first_bill_no is not set, set it to the current 'Bill No.' value
                    if first_bill_no is None:
                        first_bill_no = row['Bill No.']
                    
                    # Assign the first_bill_no value to 'short_name'
                    df.at[index, 'short_name'] = first_bill_no

                # Keep only the rows where 'Type' is 'OB' or 'SB' after the loop
                df = df[df['Type'].isin(['OB', 'SB'])]

                # Apply the lambda function to 'short_name' based on the condition
                df['short_name'] = df['short_name'].apply(lambda x: x.rsplit('-', 1)[0] if x.startswith('L') else x.split('-', 1)[0])


                # Apply the lambda function to 'short_name' to remove leading zeros
                df['short_name'] = df['short_name'].apply(lambda x: x.lstrip('0') if x[0].isdigit() else x)
                
                # Apply the convert_date_format function to 'Date' and 'Due Date' columns
                df['Date'] = df['Date'].apply(convert_date_format)

                # Copy 'Date' data to 'Due Date' column
                df['Due Date'] = df['Date']                

                # Apply the convert_nepali_to_ad function to the 'Date' column
                df['Date'] = df['Date'].apply(convert_nepali_to_ad)
                
                # Apply the convert_nepali_to_ad function to the 'Due Date' column
                df['Due Date'] = df['Due Date'].apply(convert_nepali_to_ad)
                
                #Delete the Date column
                df.drop(columns=['Date'], inplace=True)

                #Delete the Date column
                df.drop(columns=['Days'], inplace=True)

                # Define the new column names
                new_column_names = [
                    'type',
                    'bill_no',
                    'due_date',
                    'inv_amount',
                    'cycle1',
                    'cycle2',
                    'cycle3',
                    'cycle4',
                    'cycle5',
                    'cycle6',
                    'cycle7',
                    'cycle8',
                    'cycle9',
                    'balance',
                    'short_name'
                ]

                # Create a dictionary mapping old column names to new column names
                column_mapping = dict(zip(df.columns, new_column_names))

                # Rename columns
                df = df.rename(columns=column_mapping)
                
                 # Calculate the balance directly in the DataFrame
                df['balance'] = df[['cycle1', 'cycle2', 'cycle3', 'cycle4', 'cycle5', 'cycle6', 'cycle7', 'cycle8', 'cycle9']].sum(axis=1)

                # Assuming df is your DataFrame
                df.to_excel('sorted_aging_report.xlsx', index=False)

                # Create a link to download the file
                FileLink('sorted_aging_report.xlsx')

                # Fetch all clients at once
                short_names = df['short_name'].astype(str).str.strip().unique()
                clients = Client.objects.filter(short_name__in=short_names)

                success_count = 0
                
                

                for index, row in df.iterrows():
                    try:
                        short_name_value = row['short_name'].strip()
                        client = clients.get(short_name=short_name_value)
                        
                        # Check if a Bill with the same data already exists
                        existing_bill = Bill.objects.filter(
                            type=row['type'],
                            bill_no=row['bill_no'],
                            due_date=row['due_date'],
                            short_name=client,
                        ).first()

                        if existing_bill:
                            # Update existing Bill with new data
                            existing_bill.type = row['type']
                            existing_bill.due_date = row['due_date']
                            existing_bill.inv_amount = row['inv_amount']
                            existing_bill.cycle1 = row['cycle1']
                            existing_bill.cycle2 = row['cycle2']
                            existing_bill.cycle3 = row['cycle3']
                            existing_bill.cycle4 = row['cycle4']
                            existing_bill.cycle5 = row['cycle5']
                            existing_bill.cycle6 = row['cycle6']
                            existing_bill.cycle7 = row['cycle7']
                            existing_bill.cycle8 = row['cycle8']
                            existing_bill.cycle9 = row['cycle9']
                            existing_bill.balance = row['balance']

                            # Save the changes
                            existing_bill.save()
                            # Call the functions to update the client's balance and overdue120
                            update_client_balance(existing_bill.short_name)
                            overdue120d(existing_bill.short_name)
                            continue
                        
                        # Create a new Bill instance
                        Bill.objects.create(
                            type=row['type'],
                            bill_no=row['bill_no'],
                            due_date=row['due_date'],
                            inv_amount=row['inv_amount'],
                            cycle1=row['cycle1'],
                            cycle2=row['cycle2'],
                            cycle3=row['cycle3'],
                            cycle4=row['cycle4'],
                            cycle5=row['cycle5'],
                            cycle6=row['cycle6'],
                            cycle7=row['cycle7'],
                            cycle8=row['cycle8'],
                            cycle9=row['cycle9'],
                            balance=row['balance'],
                            short_name=client,
                        )
                        success_count += 1
                        # Call the function to update the client's balance after each Bill creation
                        update_client_balance(client)
                        overdue120d(client)
                        
                        # Call the function to create actions for due bills
                        create_actions_for_due_bills()
                        
                        
                        
                    except Client.DoesNotExist:
                        error_messages.append(f'Client "{short_name_value}" not found at row {index + 2}\n')
                    except ValidationError as e:
                        error_messages.append(f'Validation error at row {index + 2}: {e}\n')
                
                
                if success_count > 0:
                    success_messages.append(f"{success_count} records successfully uploaded.")
                    download_link = reverse('download_excel')
                else:
                    download_link = None
                    
                for success_message in success_messages:
                    messages.success(request, success_message)
                for error_message in error_messages:
                    messages.error(request, error_message)
                    
                return redirect('upload_excel')

            except Exception as e:
                error_messages.append(f'Error processing Excel file: {e}')
        
    else:
        form = ExcelUploadForm()

    context = {
        'form': form,
        'download_link': download_link,
    }

    for success_message in success_messages:
            messages.success(request, success_message)
    for error_message in error_messages:
        messages.error(request, error_message)

    return render(request, 'upload.html', context)

def collection(request):
    clients = Client.objects.all()
    actions = Action.objects.all() 
    
    # Calculate the count of manual actions that are not completed
    manual_not_completed_count = Action.objects.filter(type='manual', completed=False).count()
    auto_count = Action.objects.filter(type='auto', completed=False).count()
   

    
    # Set the initial value of the "Action Date" field to today's date
    today_date = date.today()
    add_form = ActionCreationForm(initial={'action_date': today_date})
    update_form = ActionUpdateForm()
    
    if request.method == 'POST':
        # Check if the form submitted is the ActionCreationForm
        if 'add_action' in request.POST:
            add_form = ActionCreationForm(request.POST)
            if add_form.is_valid():
                
                # Redirect to the same view to avoid resubmitting the form on page reload
                add_form.save()
                return redirect('collection')

        # Check if the form submitted is the ActionUpdateForm
        elif 'update_actions' in request.POST:
            update_form = ActionUpdateForm(request.POST)
            if update_form.is_valid():
                selected_actions_ids = request.POST.getlist('completed_actions')
                
                # Convert the list of strings to a list of integers
                selected_actions_ids = [int(action_id) for action_id in selected_actions_ids]

                # Update the completion status of selected actions
                Action.objects.filter(id__in=selected_actions_ids).update(completed=True)

                # Recalculate the counts after the update
                manual_not_completed_count = Action.objects.filter(type='manual', completed=False).count()
                auto_count = Action.objects.filter(type='auto', completed=False).count()

                # Redirect to the same view to avoid resubmitting the form on page reload
                return redirect('collection')
    else:
        add_form = ActionCreationForm()
        update_form = ActionUpdateForm()

    context = {'actions': actions, 
               'clients': clients,
               'manual_not_completed_count': manual_not_completed_count, 
               'auto_count': auto_count,
               'add_form': add_form,
               'update_form': update_form}
    return render(request, 'collection.html', context)

def overdue120d(client):
    # Get the sum of all cycles for the client's bills
    total_cycles_sum = Bill.objects.filter(short_name=client).aggregate(
        total_cycles_sum=Sum('cycle9'))['total_cycles_sum'] or Decimal('0.00')

    # Round the total_cycles_sum to two decimal places
    total_cycles_sum = round(total_cycles_sum, 2)

    # Update the overdue120 field in the Client model
    client.overdue120 = total_cycles_sum
    client.save()

def download_excel(request):
    file_path = 'sorted_aging_report.xlsx'
    if default_storage.exists(file_path):
        with default_storage.open(file_path, 'rb') as excel_file:
            response = HttpResponse(excel_file.read(), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="{file_path}"'
            return response
    else:
        return HttpResponse("File not found", status=404)
    
def update_client_balance(client):
    # Get the sum of the 'balance' field for the client's bills
    total_balance_sum = Bill.objects.filter(short_name=client).aggregate(
        total_balance_sum=Sum('balance')
    )['total_balance_sum'] or Decimal('0.00')

    # Round the total_balance_sum to two decimal places
    total_balance_sum = round(total_balance_sum, 2)

    # Update the balance field in the Client model
    client.balance = total_balance_sum
    client.save()
   
def client(request):
    clients = Client.objects.all()
    return render(request , 'client.html' ,  {'clients': clients})

def client_profile(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    bills = client.bill_set.all()  # Assuming you have a related name 'bill_set' in your Client model
    return render(request, 'client_profile.html', {'client': client, 'bills': bills})

def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid(): 
            form.save()
            return redirect('client')  # Redirect to a success page or another view
    else:
        form = ClientForm(instance=client)

    return render(request, 'edit_client.html', {'form': form, 'client': client})

def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    client.delete()
    messages.success(request, 'Client has been deleted successfully!')
    return redirect('client')

def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client')  # Redirect to a success page or another view
    else:
        form = ClientForm()

    return render(request, 'add_client.html', {'form': form, 'client': None})

def create_actions_for_due_bills():
    # Get today's date
    today = timezone.now().date()

    # Define the due date differences and corresponding action types
    due_date_diff_types = [
        (3, 'SMS', 'auto'),
        (5, 'SMS', 'auto'),
        (6, 'Call', 'manual'),
    ]

    # Iterate through the due date differences and create actions for bills
    for due_date_diff, action_type, action_mode in due_date_diff_types:
        # Calculate the target date based on the due date difference
        target_date = today - timedelta(days=due_date_diff)

        # Get overdue bills with due dates equal to the target date
        bills_to_process = Bill.objects.filter(due_date=target_date, balance__gt=0)

        # Iterate through bills and create actions
        for bill in bills_to_process:
            # Check if an action for the same bill, action type, and mode already exists
            existing_action = Action.objects.filter(
                bill_no=bill.bill_no,
                action_type=action_type,
                type='manual' if action_mode == 'manual' else 'auto'
            ).first()

            # Create the action only if it doesn't already exist
            if not existing_action:
                Action.objects.create(
                    action_date=today,
                    type='manual' if action_mode == 'manual' else 'auto',
                    action_type=action_type,
                    action_amount=bill.balance,
                    short_name=bill.short_name,
                    bill_no=bill.bill_no,
                    completed=False
                )

def get_client_names(request):
    # Query all clients and their associated bill numbers
    client_data = (
        Client.objects
        .values('account_name')
        .annotate(bill_numbers=F('bill__bill_no')).distinct()
    )

    # Convert QuerySet to a list of dictionaries
    client_data_list = list(client_data)

    # Iterate over the list and fetch all unique bill numbers for each client
    for client in client_data_list:
        # Use a set to ensure uniqueness of bill numbers
        unique_bill_numbers = set(Bill.objects.filter(short_name__account_name=client['account_name']).values_list('bill_no', flat=True))
        client['bill_numbers'] = list(unique_bill_numbers)

    return JsonResponse({'client_data': client_data_list}, encoder=DjangoJSONEncoder, safe=False)

# AJAX
def load_bills(request):
    client_id = request.GET.get('client_id')
    client = get_object_or_404(Client, pk=client_id)
    bills = Bill.objects.filter(short_name=client).order_by('bill_no')
    
    options = '<option value="">---------</option>'
    for bill in bills:
        options += f'<option value="{bill.id}">{bill.bill_no}</option>'
    
    return HttpResponse(options)


    
