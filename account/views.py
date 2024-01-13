from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import timedelta
from sales.views import calculate_percentages, calculate_total_cycles_for_client
from .utils import detectUser
from django.core.exceptions import PermissionDenied
from django.utils.http import urlsafe_base64_decode
from .models import User
from .utils import detectUser, send_verification_email
from django.contrib.auth.tokens import default_token_generator
from sales.models import Client,Bill,Action,DailyBalance,UserBalance,CompanyBalance
from django.db.models import Sum, F, Max, Q
import json
from django.http import JsonResponse
from django.utils import timezone
# Create your views here.


# Restrict the vendor from accessing the customer page
def check_role_admin(user):
    if user.role == 1:
        return True
    else:
        raise PermissionDenied


# Restrict the customer from accessing the vendor page
def check_role_user(user):
    if user.role == 2:
        return True
    else:
        raise PermissionDenied

def login(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in!')
        return redirect('account:myAccount')

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')

        # Authenticate using the custom user model
        user = authenticate(request, username=phone_number, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, 'You are now logged in.')
            return redirect('account:myAccount')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    return render(request, 'login.html')


#Logout
def logout(request):
   auth.logout(request)
   messages.info(request, 'You are logged out.')
   return redirect('login')

#Dashboard Assign
@login_required(login_url='account:login')
def myAccount(request):
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)

#userdashboard
@login_required(login_url='account:login')
@user_passes_test(check_role_user)
def userdashboard(request):
    # Retrieve the logged-in user
    user = request.user
    collector_count = Action.objects.filter(completed=False, short_name__collector=request.user).count() 
    
    # Filter clients for the currently logged-in user
    clients = Client.objects.filter(collector=user)

    # Calculate total cycles for each client
    total_cycles_by_client = {client.id: calculate_total_cycles_for_client(client) for client in clients}

    # Filter bills for the clients associated with the logged-in user
    bills = Bill.objects.filter(short_name__collector=request.user)
    
    # Calculate the date 15 days ago
    fifteen_days_ago = timezone.now() - timedelta(days=15)

    # Filter daily balances for the last 15 days
    daily_balances = DailyBalance.objects.filter(collector=user, date__gte=fifteen_days_ago).order_by('date')

    # Prepare data for Morris Line Chart
    chart_data = []
    for daily_balance in daily_balances:
        chart_data.append({
            'y': daily_balance.date.strftime('%Y-%m-%d'),
            'balance': float(daily_balance.total_balance),
        })
        
    
    mycollection=UserBalance.objects.get(user=user)
    
    # Calculate aging data
    aging_data = {f'cycle{i}': bills.aggregate(Sum(f'cycle{i}'))[f'cycle{i}__sum'] or 0 for i in range(1, 10)}

    # Calculate the total sum of all bills
    total_sum = sum(aging_data.values())

    # Calculate the grand total sum of all bills' balance
    grand_total_balance = bills.aggregate(Sum('balance'))['balance__sum'] or 0

    # Calculate percentages based on grand total balance
    percentages = calculate_percentages(aging_data, grand_total_balance)
    
    # Get the top 5 clients with the highest balance
    top_clients = clients.order_by('-balance')[:5]

    context = {
        'user': user,
        'clients': clients,
        'aging_data': aging_data,
        'total_sum': total_sum,
        'grand_total_balance': grand_total_balance,
        'percentages': percentages,
        'total_cycles_by_client': total_cycles_by_client,
        'top_clients': top_clients,
        'collector_count': collector_count,
        'chart_data': chart_data,
        'mycollection':mycollection,
    }

    return render(request, 'user_dash.html', context)


#admindashboard
@login_required(login_url='account:login')
@user_passes_test(check_role_admin)
def admindashboard(request):
    # Filter clients for the currently logged-in user
    clients = Client.objects.all()
    bills = Bill.objects.all()
    collector = User.objects.filter(role=2)
    total_collector = collector.count
    # Calculate the grand total sum of all bills' balance
    total_balance = bills.aggregate(Sum('balance'))['balance__sum'] or 0

    # Round the total_overdue to 2 decimal places
    total_overdue = round(total_balance, 2)

    top_clients = clients.order_by('-balance')[:5]

    collector_data = {}

    for client in clients:
        collector = client.collector
        if collector:
            total_due = Bill.objects.filter(short_name=client).aggregate(Sum('balance'))['balance__sum'] or 0
            if collector.user_name in collector_data:
                collector_data[collector.user_name] += total_due
            else:
                collector_data[collector.user_name] = total_due
    

    # Filter daily balances for the last 15 days
    daily_balances = DailyBalance.objects.order_by('date')

    # Prepare data for Morris Line Chart
        # Prepare data for Morris Line Chart
    chart_data = []

    for daily_balance in daily_balances:
        collector_name = daily_balance.collector.user_name  # Assuming collector is a ForeignKey to User

        data_point = {
            'y': daily_balance.date.strftime('%Y-%m-%d'),
            'balance': float(daily_balance.total_balance),
        }

        # Check if collector_name is already present in chart_data
        collector_exists = any(collector['collector'] == collector_name for collector in chart_data)

        if collector_exists:
            # If collector is present, append data_point to its data array
            for collector in chart_data:
                if collector['collector'] == collector_name:
                    collector['data'].append(data_point)
        else:
            # If collector is not present, add a new entry with collector name and data array
            chart_data.append({
                'collector': collector_name,
                'data': [data_point],
            })
    
    company_balance = CompanyBalance.objects.order_by('date')
    # Prepare data for Morris Line Chart
    company_data = []
    for company_balance in company_balance:
        company_data.append({
            'y': company_balance.date.strftime('%Y-%m-%d'),
            'total_balance': float(company_balance.total_balance),
        })
    context = {
        'clients' : clients ,
        'total_overdue' : total_overdue ,
        'collector' : collector ,
        'total_collector' : total_collector ,
        'top_clients' : top_clients ,
        'collector' : collector ,
        'collector_data': collector_data ,
        'chart_data': json.dumps(chart_data),
        'company_data':company_data,
        
    }
    return render(request ,'admin_dash.html', context)


#forgot Password Link
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']

        if User.objects.filter(email=email).exists():
            
            user =  User.objects.get(email=email)

            # send reset password email
            mail_subject = 'Reset Your Password'
            email_template = 'emails/reset_password_email.html'
            send_verification_email(request, user, mail_subject, email_template)

            messages.success(request, 'Password reset link has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist')
            return redirect('account:forgot_password')
    return render(request, 'forgot_password.html')


def reset_password_validate(request, uidb64, token):
    # validate the user by decoding the token and user pk
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.info(request, 'Please reset your password')
        return redirect('account:reset_password')
    else:
        messages.error(request, 'This link has been expired!')
        return redirect('account:myAccount')


def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            pk = request.session.get('uid')
            user = User.objects.get(pk=pk)
            user.set_password(password)
            user.is_active = True
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Password do not match!')
            return redirect('account:reset_password')
    return render(request, 'reset_password.html')



    
    
