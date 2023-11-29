from django.urls import path, include
from . import views
app_name ='account'
urlpatterns =[
path('login/', views.login, name='login'),
path('logout/',views.logout, name='logout'),
path('myAccount/',views.myAccount, name='myAccount'),
path('admindashboard/',views.admindashboard, name='admindashboard'),
path('userdashboard/',views.userdashboard, name='userdashboard'),
]