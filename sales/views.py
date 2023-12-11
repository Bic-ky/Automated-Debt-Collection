from django.forms import ValidationError
from django.shortcuts import render
from . models import Client,Bill
from .resources import BillResource
from django.contrib import messages
from tablib import Dataset
from .forms import ExcelUploadForm  
from django.core.exceptions import ValidationError
import pandas as pd
# Create your views here.
def profile(request):
    return render(request , 'profile.html')

def upload_excel(request):
    success_messages = []
    error_messages = []

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
                    print(error_messages)  # Make sure the error message is printed in the console
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

                # Define the new column names
                new_column_names = [
                    'type',
                    'bill_no',
                    'date',
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

                # Fetch all clients at once
                short_names = df['short_name'].astype(str).str.strip().unique()
                clients = Client.objects.filter(short_name__in=short_names)

                success_count = 0

                for index, row in df.iterrows():
                    try:
                        short_name_value = row['short_name'].strip()
                        client = clients.get(short_name=short_name_value)

                        Bill.objects.create(
                            type=row['type'],
                            bill_no=row['bill_no'],
                            date=row['date'],
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

            except Exception as e:
                error_messages.append(f'Error processing Excel file: {e}')
    else:
        form = ExcelUploadForm()

    for success_message in success_messages:
        messages.success(request, success_message)

    for error_message in error_messages:
        messages.error(request, error_message)

    return render(request, 'upload.html', {'form': form})






