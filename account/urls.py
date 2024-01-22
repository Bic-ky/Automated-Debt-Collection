from django.urls import path, include
from . import views

app_name ='account'
urlpatterns =[
path('logout/',views.logout, name='logout'),


path('myAccount/',views.myAccount, name='myAccount'),
path('admindashboard/',views.admindashboard, name='admindashboard'),
path('userdashboard/',views.userdashboard, name='userdashboard'),

path('user_change_password/', views.user_change_password, name='user_change_password'),
path('admin_change_password/', views.admin_change_password, name='admin_change_password'),


path('forgot_password/', views.forgot_password, name='forgot_password'),
path('reset_password_validate/<uidb64>/<token>/', views.reset_password_validate, name='reset_password_validate'),
path('reset_password/', views.reset_password, name='reset_password'),

]