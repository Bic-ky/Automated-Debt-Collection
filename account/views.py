from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from .utils import detectUser
from django.core.exceptions import PermissionDenied
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
            return redirect('account:login')

    return render(request, 'login.html')


#Logout
def logout(request):
   auth.logout(request)
   messages.info(request, 'You are logged out.')
   return redirect('account:login')

@login_required(login_url='account:login')
#Dashboard Assign
def myAccount(request):
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)


@login_required(login_url='account:login')
@user_passes_test(check_role_user)
def userdashboard(request):
    return render(request ,'user_dash.html')


@login_required(login_url='account:login')
@user_passes_test(check_role_admin)
def admindashboard(request):
    return render(request ,'admin_dash.html')