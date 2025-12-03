from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_pdf, name='upload_pdf'),
    path('progress/<str:task_id>/', views.check_progress, name='check_progress'),
    path('download/<str:task_id>/', views.download_file, name='download_file'),
]
