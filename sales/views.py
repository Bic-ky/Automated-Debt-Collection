from django.forms import ValidationError
from datetime import datetime, timedelta, date
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Action
from .filters import ActionFilter
from .models import Client, Bill, Action,User,DailyBalance,UserBalance
from .resources import BillResource
from django.contrib import messages
from .forms import ExcelUploadForm, ClientForm, ActionUpdateForm, ActionCreationForm, ExtendActionForm,SendSMSForm
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.core.files.storage import default_storage
from nepali_date_converter import english_to_nepali_converter, nepali_to_english_converter
from django.db.models import Sum, F, Max, Q
from decimal import Decimal
from IPython.display import FileLink
from django.utils import timezone
import pandas as pd
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder
import logging
from django.template import Context, Template
import json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib import messages


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
                            calculate_total_balance_for_all_collectors()
                            update_collector_balances()
                            delete_actions()                            
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
                        calculate_total_balance_for_all_collectors()
                        update_collector_balances()
                                                   
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
                
                update_subject = 'Excel File Update Notification'
                update_message = f'The Excel file has been successfully uploaded on {timezone.now()}'
                send_update_email(update_subject, update_message) 
                
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
     # Filter clients for the currently logged-in user
    clients = Client.objects.filter(collector=request.user)

    # Filter actions for the currently logged-in user
    actions = Action.objects.filter(short_name__collector=request.user).order_by('-created')
    
    
    # Calculate the count of manual actions that are not completed
    manual_not_completed_count = Action.objects.filter(type='manual', completed=False).count()
    auto_count = Action.objects.filter(type='auto', completed=False).count()
   
    # Set the initial value of the "Action Date" field to today's date
    today_date = date.today()
    add_form = ActionCreationForm(initial={'action_date': today_date})
    update_form = ActionUpdateForm()
    if request.method == 'POST':
        
        if 'add_action' in request.POST:
            action_type = request.POST.get('action_type')
            
            short_name_id = request.POST.get('short_name')
            description=request.POST.get('description')
            subtype=request.POST.get('subtype')
            followup_date=request.POST.get('followup_date')
            completed=request.POST.get('completed')
            if followup_date=='':
                followup_date=None
            if completed =='on':
               completed=True
            else:
                completed=False
            # Validate that required fields are present
            if not (action_type ):
                messages.error(request, 'Action type is  required')
                return redirect('collection')

            # Fetch the related objects
            try:
                
                short_name = Client.objects.get(pk=short_name_id)
            except (Bill.DoesNotExist, Client.DoesNotExist):
                messages.error(request, 'Invalid bill number or short name.')
                return redirect('collection')

            # Set the action_amount to the balance of the corresponding bill
            action_amount = short_name.balance if hasattr(short_name, 'balance') else 0

            type = 'manual'  # Set the type to 'manual'

            # Create an Action instance and save it to the database
            action_instance = Action(
                action_date=today_date,
                type=type,
                action_type=action_type,
                action_amount=action_amount,
                short_name=short_name,
                followup_date=followup_date,
                description=description,
                subtype=subtype,
                completed=completed,
            )
            action_instance.save()

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
    actions = Action.objects.filter(short_name=client).order_by('-created')
    bills = Bill.objects.filter(short_name=client)
    cyclebills = client.bill_set.all()

    # Calculate the sum of amounts for each aging bucket
    aging_data = {
        'cycle1': cyclebills.aggregate(Sum('cycle1'))['cycle1__sum'] or Decimal(0),
        'cycle2': cyclebills.aggregate(Sum('cycle2'))['cycle2__sum'] or Decimal(0),
        'cycle3': cyclebills.aggregate(Sum('cycle3'))['cycle3__sum'] or Decimal(0),
        'cycle4': cyclebills.aggregate(Sum('cycle4'))['cycle4__sum'] or Decimal(0),
        'cycle5': cyclebills.aggregate(Sum('cycle5'))['cycle5__sum'] or Decimal(0),
        'cycle6': cyclebills.aggregate(Sum('cycle6'))['cycle6__sum'] or Decimal(0),
        'cycle7': cyclebills.aggregate(Sum('cycle7'))['cycle7__sum'] or Decimal(0),
        'cycle8': cyclebills.aggregate(Sum('cycle8'))['cycle8__sum'] or Decimal(0),
        'cycle9': cyclebills.aggregate(Sum('cycle9'))['cycle9__sum'] or Decimal(0),
    }

    # Check if all actions for the client have completed=True
    all_actions_completed = all(action.completed for action in actions)

    incomplete_actions = []  # Initialize as an empty list

    if all_actions_completed:
        # If all actions are completed, store the last action
        last_action = actions.first()
    else:
        # If not all actions are completed, filter and store only the incomplete ones
        incomplete_actions = [action for action in actions if not action.completed]
        last_action = None  # Initialize to None, in case there are no incomplete actions

   

    total_amount = client.balance
    # Calculate percentages based on grand total balance
    percentages = calculate_percentages(aging_data, total_amount)
    
    
    if request.method == 'POST':
        sms_form = SendSMSForm(request.POST)
        if sms_form.is_valid():
            # Process the form data
            description = sms_form.cleaned_data['description']
            subtype = sms_form.cleaned_data['subtype']
            phone_number = sms_form.cleaned_data['phone_number']

            # Perform additional actions with the SMS data
            # For example, log the SMS action in the database
            Action.objects.create(
                action_date=timezone.now(),
                type='manual',
                action_type='SMS',
                action_amount=client.balance,  
                short_name=client,
                subtype=subtype,
                description=description,
                completed=True,
                
            )

            # Send the SMS using an external service 
            send_sms(phone_number, description)

            # Redirect or render a response as needed
            return redirect(request.path)
    else:
        # Assuming you have access to the client's phone number
        initial_phone_number = client.phone_number if client.phone_number else ''
        sms_form = SendSMSForm(initial={'phone_number': initial_phone_number})


    context = {
        'client': client,
        'actions': actions,
        'last_action': last_action,
        'incomplete_actions': incomplete_actions,
        'cyclebills': cyclebills,
        'aging_data': aging_data,
        'percentages': percentages,
        'bills': bills,
        'sms_form':sms_form,
        
    }

    return render(request, 'client_profile.html', context)

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
       
@receiver(post_save, sender=Bill)
def create_actions_for_due_bills(sender, instance, created, **kwargs):
    # Only proceed if a new bill is created
    if created:
        # Get today's date
        today = timezone.now().date()

        # Calculate target_date
        target_date = instance.due_date + timedelta(days=instance.short_name.grant_period)

        # Create Action 1
        Action.objects.create(
            action_date=target_date,
            type='auto',
            action_type='SMS',
            action_amount=instance.short_name.balance,
            short_name=instance.short_name,
            completed=False,
            subtype='Reminder'
        )

        # Create Action 2
        Action.objects.create(
            action_date=target_date + timedelta(days=1),
            type='auto',
            action_type='SMS',
            action_amount=instance.short_name.balance,
            short_name=instance.short_name,
            completed=False,
            subtype='Gentle'
        )

        # Create Action 3
        Action.objects.create(
            action_date=target_date + timedelta(days=3),
            type='auto',
            action_type='SMS',
            action_amount=instance.short_name.balance,
            short_name=instance.short_name,
            bill_no=instance,
            completed=False,
            subtype='Strong'
        )

        # Create Action 4 (if group is 'Normal')
        if instance.short_name.group == 'Normal':
            Action.objects.create(
                action_date=target_date + timedelta(days=7),
                type='auto',
                action_type='SMS',
                action_amount=instance.short_name.balance,
                short_name=instance.short_name,
                completed=False,
                subtype='Final'
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

def send_sms(phone_number, sms_content, simulate_success=False):
    if simulate_success:
        # Simulate a successful response without making the actual API call
        print(f"Simulated success: SMS content for {phone_number}: {sms_content}")
        return True, "Simulated success: SMS content printed"

    url = "https://api.sparrowsms.com/v2/sms/"
    data = {
        'token': 'v2_M1vtw2aeNOXETkVFSgoOXmOchwN.BqR',
        'from': 'Demo',
        'to': phone_number,
        'text': sms_content,
    }

    response = requests.post(url, data=data)

    if response.status_code == 200:
        # If SMS is successfully sent, return a tuple indicating success
        return True, response.text
    else:
        # If there is an error, return a tuple indicating failure
        return False, response.text

@receiver(post_save, sender=Action)
def check_and_trigger_sms(sender, instance, **kwargs):
    # Disconnect the signal to prevent it from triggering multiple times
    post_save.disconnect(check_and_trigger_sms, sender=Action)
    
    today = timezone.now().date()

    # Check if the action type is 'auto' and action_type is 'SMS'
    if instance.type == 'auto' and instance.action_type == 'SMS' and instance.action_date >= today and not instance.completed: 
        try:
            # Fetch related client and bill
            client = instance.short_name

            # Get dynamic SMS content based on subtype
            sms_content = generate_sms_text(instance.subtype, client)

            # Trigger send_sms function
            success, response_text = send_sms(client.phone_number, sms_content)

            if success:
                # Update the 'completed' field to True if SMS is sent successfully
                # Check if 'completed' is already True before updating
                if not instance.completed:
                    instance.completed = True
                    instance.description = sms_content
                    instance.save()
            else:
                # If sending SMS fails, update the instance description with the "response" part
                try:
                    response_json = json.loads(response_text)
                    instance.description = response_json.get("response", response_text)
                except json.JSONDecodeError:
                    instance.description = response_text

                # Optionally, you may log the error or take other actions if needed
                print(f"SMS sending failed. Response: {response_text}")
                instance.save()

        except ObjectDoesNotExist:
            # Handle the case where the related client is not found
            print("Client not found for the given Action.")

        except Exception as e:
            # Handle any other exceptions that might occur
            print(f"Error occurred: {e}")

    # Reconnect the signal after processing
    post_save.connect(check_and_trigger_sms, sender=Action)

def generate_sms_text(subtype, client):
    # Default agent name (you can replace it with actual agent name)
    agent_name = client.collector.full_name if client.collector else "Accounts Team"

    # Default contact number (you can replace it with actual contact number)
    contact_number = "9800000001"

    # Initialize template string based on subtype
    template_str = ""

    if subtype == 'Reminder':
        template_str = "Dear {{ client.account_name }}, This is {{ agent_name }} from SparrowSMS. We'd like to remind you that payment for Nrs. {{ client.balance }} is due. For more information, call {{ contact_number }}."

    elif subtype == 'Gentle':
        template_str = "Dear {{ client.account_name }},A gentle reminder of payment Rs{{ client.balance }} is pending. Please send the payment and contact: {{ agent_name }} SPARROW SMS."

    elif subtype == 'Strong':
        template_str = "Dear {{ client.account_name }}, we still have not received Nrs {{ bill.balance }} payment . We request you to make the payment as soon as possible. {{ contact_number }} SPARROW SMS."

    elif subtype == 'Final':
        template_str = "Dear {{ client.account_name }}, after several attempts and reminders, we have not received the due Nrs. {{ bill.balance }}. Unfortunately, service will be blocked. Contact us at {{ contact_number }}."

    else:
        return "Unknown subtype."

    # Render the template with dynamic data
    template = Template(template_str)
    context = Context({'client': client, 'agent_name': agent_name, 'contact_number': contact_number})
    return template.render(context)



def action(request):
    clients = Client.objects.all()
    actions = Action.objects.all().order_by('-created')

    # Process the date range filter
    date_from = request.GET.get('action_date_from')
    date_to = request.GET.get('action_date_to')

    if date_from and date_to:
        date_from = datetime.strptime(date_from, "%Y-%m-%d")
        date_to = datetime.strptime(date_to, "%Y-%m-%d")
        actions = actions.filter(action_date__range=[date_from, date_to])
    
    # Calculate the count of manual actions that are not completed
    manual_not_completed_count = Action.objects.filter(type='manual', completed=False).count()
    auto_count = Action.objects.filter(type='auto', completed=False , pause=False).count()
   
    # Set the initial value of the "Action Date" field to today's date
    today_date = date.today()

    action_filter = ActionFilter(request.GET, queryset=actions)
    actions = action_filter.qs


    context = {'actions': actions, 
               'clients': clients,
               'manual_not_completed_count': manual_not_completed_count, 
               'auto_count': auto_count,
               'action_filter': action_filter, 
                }
   
    return render(request, 'action.html' , context)




def calculate_total_cycles_for_client(client):
    return {
        'cycle1': Bill.objects.filter(short_name=client).aggregate(Sum('cycle1'))['cycle1__sum'] or 0,
        'cycle2': Bill.objects.filter(short_name=client).aggregate(Sum('cycle2'))['cycle2__sum'] or 0,
        'cycle3': Bill.objects.filter(short_name=client).aggregate(Sum('cycle3'))['cycle3__sum'] or 0,
        'cycle4': Bill.objects.filter(short_name=client).aggregate(Sum('cycle4'))['cycle4__sum'] or 0,
        'cycle5': Bill.objects.filter(short_name=client).aggregate(Sum('cycle5'))['cycle5__sum'] or 0,
        'cycle6': Bill.objects.filter(short_name=client).aggregate(Sum('cycle6'))['cycle6__sum'] or 0,
        'cycle7': Bill.objects.filter(short_name=client).aggregate(Sum('cycle7'))['cycle7__sum'] or 0,
        'cycle8': Bill.objects.filter(short_name=client).aggregate(Sum('cycle8'))['cycle8__sum'] or 0,
        'cycle9': Bill.objects.filter(short_name=client).aggregate(Sum('cycle9'))['cycle9__sum'] or 0,
    }

def aging(request):
    clients = Client.objects.all()
    # Calculate the sum of amounts for each aging bucket
    # Dictionary to store total cycles for each client
    total_cycles_by_client = {}

    for client in clients:
        total_cycles_by_client[client.id] = calculate_total_cycles_for_client(client)

    aging_data = {
        'cycle1': Bill.objects.aggregate(Sum('cycle1'))['cycle1__sum'] or 0,
        'cycle2': Bill.objects.aggregate(Sum('cycle2'))['cycle2__sum'] or 0,
        'cycle3': Bill.objects.aggregate(Sum('cycle3'))['cycle3__sum'] or 0,
        'cycle4': Bill.objects.aggregate(Sum('cycle4'))['cycle4__sum'] or 0,
        'cycle5': Bill.objects.aggregate(Sum('cycle5'))['cycle5__sum'] or 0,
        'cycle6': Bill.objects.aggregate(Sum('cycle6'))['cycle6__sum'] or 0,
        'cycle7': Bill.objects.aggregate(Sum('cycle7'))['cycle7__sum'] or 0,
        'cycle8': Bill.objects.aggregate(Sum('cycle8'))['cycle8__sum'] or 0,
        'cycle9': Bill.objects.aggregate(Sum('cycle9'))['cycle9__sum'] or 0,
    }

    # Calculate the total sum of all bills
    total_sum = sum(aging_data.values())
    # Calculate the grand total sum of all bills' balance
    grand_total_balance = Bill.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    
    # Calculate percentages based on grand total balance
    percentages = calculate_percentages(aging_data, grand_total_balance)

    context = {
        'aging_data': aging_data,
        'total_sum': total_sum,
        'grand_total_balance': grand_total_balance,
        'percentages': percentages,
        'clients':clients,
        'total_cycles_by_client': total_cycles_by_client,
    }

    return render(request, 'aging.html', context)

def calculate_percentages(aging_data, total_amount):
    percentage_0_30_days = round((float(aging_data['cycle1']) / float(total_amount)) * 100)
    percentage_31_60_days = round((float(aging_data['cycle2']) / float(total_amount)) * 100)
    percentage_61_90_days = round((float(aging_data['cycle3']) / float(total_amount)) * 100)
    percentage_90_days_plus = round((float(aging_data['cycle4']) + float(aging_data['cycle5']) + float(aging_data['cycle6']) + float(aging_data['cycle7']) + float(aging_data['cycle8']) + float(aging_data['cycle9'])) / float(total_amount) * 100)
    
    return {
        'percentage_0_30_days': percentage_0_30_days,
        'percentage_31_60_days': percentage_31_60_days,
        'percentage_61_90_days': percentage_61_90_days,
        'percentage_90_days_plus': percentage_90_days_plus,
    }
    
def delete_actions():
    # Fetch actions that meet the deletion criteria
    actions_to_delete = Action.objects.filter(
        completed=False,
        type='auto',
        bill_no__balance__lte=300
    )

    # Delete the selected actions
    actions_to_delete.delete()

def calculate_total_balance_for_all_collectors():
    today = date.today()

    # Get all collectors
    collectors = User.objects.filter(role=User.USER)

    for collector in collectors:
        # Calculate the total balance for all clients of the collector in the last 15 days
        total_balance = Client.objects.filter(collector=collector).aggregate(
            total_balance=Sum('balance')
        )['total_balance'] or 0

        # Check if a DailyBalance entry already exists for today and this collector
        daily_balance_entry = DailyBalance.objects.filter(collector=collector, date=today).first()

        if daily_balance_entry:
            # Update existing DailyBalance entry with new total_balance
            daily_balance_entry.total_balance = total_balance
            daily_balance_entry.save()
        else:
            # Create a new DailyBalance entry
            DailyBalance.objects.create(collector=collector, total_balance=total_balance, date=today)

<<<<<<< Updated upstream
def update_collector_balances():
    # Get all collectors (users with role USER)
    collectors = User.objects.filter(role=User.USER)

    # Calculate yesterday's date
    yesterday = datetime.now().date() - timedelta(days=1)

    for collector in collectors:
        # Get or create UserBalance for the collector
        user_balance, created = UserBalance.objects.get_or_create(user=collector)

        # Get yesterday's balance
        yesterday_balance = DailyBalance.objects.filter(
            collector=collector,
            date=yesterday
        ).values('total_balance').first()

        # Get today's balance
        today_balance = DailyBalance.objects.filter(
            collector=collector,
            date=datetime.now().date()
        ).values('total_balance').first()

        if yesterday_balance and today_balance:
            # Calculate the difference as yesterday's balance minus today's balance
            balance_difference = yesterday_balance['total_balance'] - today_balance['total_balance']

            if balance_difference > 0:
                # Update collector_balance by subtracting the positive difference
                user_balance.collector_balance = F('collector_balance') + balance_difference
                user_balance.save()

                # Update the DailyBalance for today with the new collector_balance
                DailyBalance.objects.filter(
                    collector=collector,
                    date=datetime.now().date()
                ).update(total_balance=user_balance.collector_balance)

def send_update_email(subject, message):
    
    from_email = settings.DEFAULT_FROM_EMAIL
    
    to_email = "adityachaudhary700@example.com"  
    
    # Create an EmailMessage with the subject, message, and sender/recipient information
    mail = EmailMessage(subject, message, from_email, to=[to_email])
    
    # Specify that the email content type is plain text
    mail.content_subtype = "plain"
    
    mail.send()
=======

def extend_action_dates(request, client_id):
    client = Client.objects.get(pk=client_id)
    actions = Action.objects.filter(short_name=client)

    if request.method == 'POST':
        form = ExtendActionForm(request.POST)
        if form.is_valid():
            # Process the form data and update the action dates for all actions of the client

            # Example:
            days_to_extend = form.cleaned_data['extended_date']

            for action in actions:
                # Add days_to_extend to the original action date for each action
                if days_to_extend:
                    action.action_date += timedelta(days=days_to_extend)
                    action.save()

            return redirect('client_profile', client_id=client_id)
    else:
        form = ExtendActionForm()

    context = {
        'client': client,
        'actions': actions,
        'form': form,
    }

    return render(request, 'client_profile.html', context)
>>>>>>> Stashed changes


def extend_action_dates(request, client_id):
    client = Client.objects.get(pk=client_id)
    actions = Action.objects.filter(short_name=client)

    if request.method == 'POST':
        form = ExtendActionForm(request.POST)
        if form.is_valid():
            # Process the form data and update the action dates for all actions of the client

            # Example:
            days_to_extend = form.cleaned_data['extended_date']

            for action in actions:
                # Add days_to_extend to the original action date for each action
                if days_to_extend:
                    action.action_date += timedelta(days=days_to_extend)
                    action.save()

            return redirect('client_profile', client_id=client_id)
    else:
        form = ExtendActionForm()

    context = {
        'client': client,
        'actions': actions,
        'form': form,
    }

    return render(request, 'client_profile.html', context)