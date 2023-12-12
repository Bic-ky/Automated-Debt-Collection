from django.urls import path 
from . import views

urlpatterns = [
    path('profile/', views.profile , name='profile' ),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('download_excel/', views.download_excel, name='download_excel'),

]
