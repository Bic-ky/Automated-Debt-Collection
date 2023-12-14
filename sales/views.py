from django.forms import ValidationError
from datetime import datetime
from django.shortcuts import render
from django.urls import reverse
from . models import Client,Bill
from .resources import BillResource
from django.contrib import messages
from tablib import Dataset
from .forms import ExcelUploadForm  
from django.core.exceptions import ValidationError
import pandas as pd
from IPython.display import FileLink
from django.http import FileResponse, HttpResponse
from django.core.files.storage import default_storage
from pandas.errors import EmptyDataError
from nepali_date_converter import english_to_nepali_converter, nepali_to_english_converter
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
                
                # Define the new column names
                new_column_names = [
                    'type',
                    'bill_no',
                    'due_date',
                    'days',
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
                        ).first()

                        if existing_bill:
                            # Skip creating a new Bill if an identical one already exists
                            continue

                        # Create a new Bill instance
                        Bill.objects.create(
                            type=row['type'],
                            bill_no=row['bill_no'],
                            due_date=row['due_date'],
                            days=row['days'],
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
                    except Client.DoesNotExist:
                        error_messages.append(f'Client "{short_name_value}" not found at row {index + 2}\n')
                    except ValidationError as e:
                        error_messages.append(f'Validation error at row {index + 2}: {e}\n')
                
                
                if success_count > 0:
                    success_messages.append(f"{success_count} records successfully uploaded.")
                    download_link = reverse('download_excel')
                else:
                    download_link = None

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


def download_excel(request):
    file_path = 'sorted_aging_report.xlsx'
    if default_storage.exists(file_path):
        with default_storage.open(file_path, 'rb') as excel_file:
            response = HttpResponse(excel_file.read(), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="{file_path}"'
            return response
    else:
        return HttpResponse("File not found", status=404)
    

def client(request):
    return render(request , 'client.html')