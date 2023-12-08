from django.forms import ValidationError
from django.shortcuts import render
from . models import Client,Bill
from .resources import BillResource
from django.contrib import messages
from tablib import Dataset
from django.http import HttpResponse

# Create your views here.
def profile(request):
    return render(request , 'profile.html')


# views.py
from django.shortcuts import render, redirect
import pandas as pd
from .forms import ExcelUploadForm
from .models import Bill, Client

def upload_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_data = pd.read_excel(request.FILES['file'])
            for index, row in excel_data.iterrows():
                try:
                    short_name_value = row['short_name'].strip()  # Ensure leading/trailing spaces are removed
                    client = Client.objects.get(short_name=short_name_value)
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
                except Client.DoesNotExist:
                    # Handle the case where the Client with the given short_name doesn't exist
                    print(f"Client not found for short_name '{short_name_value}' at row {index + 2}")
                except ValidationError as e:
                    # Handle invalid date format error (or any other validation errors)
                    print(f"Validation error at row {index + 2}: {e}")
                    # Optionally, you can log the error or take other appropriate actions

            return redirect('success')  # Redirect to a success page
    else:
        form = ExcelUploadForm()
    return render(request, 'upload_excel.html', {'form': form})

