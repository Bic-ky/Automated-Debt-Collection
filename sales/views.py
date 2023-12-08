from django.shortcuts import render
from . models import Client,Bill
from .resources import BillResource
from django.contrib import messages
from tablib import Dataset
from django.http import HttpResponse

# Create your views here.
def profile(request):
    return render(request , 'profile.html')


#file upload
def simple_upload(request):
    if request.method == 'POST':
        bill_resource = BillResource()
        dataset = Dataset()
        new_bill = request.FILES['myfile']

        if not new_bill.name.endswith('xlsx'):
            messages.info(request, 'wrong format')
            return render(request, 'upload.html')

        imported_data = dataset.load(new_bill.read(), format='xlsx')
        for data in imported_data:
            value = Bill(
                data[0],
                data[1],
                data[2],
                data[3],
                data[4],
                data[5],
                data[6],
                data[7],
                data[8],
                data[9],
                data[10],
                data[11],
                data[12],
                data[13],
                data[14],
                data[15],
                data[16],
                data[17],
            )
            value.save()

    return render(request, 'upload.html')
