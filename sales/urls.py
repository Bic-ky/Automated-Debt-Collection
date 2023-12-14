from django.urls import path 
from . import views

urlpatterns = [
    path('profile/', views.profile , name='profile' ),
    path('client/', views.client , name='client' ),
    path('client_profile/<int:client_id>/', views.client_profile, name='client_profile'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('download_excel/', views.download_excel, name='download_excel'),

]
