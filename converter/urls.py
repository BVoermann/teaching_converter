from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_pdf, name='upload_pdf'),
    path('progress/<str:task_id>/', views.check_progress, name='check_progress'),
    path('download/<str:task_id>/', views.download_file, name='download_file'),
    path('images-to-h5p/', views.upload_images_to_h5p, name='upload_images_to_h5p'),
    path('h5p-progress/<str:task_id>/', views.check_h5p_progress, name='check_h5p_progress'),
    path('h5p-download/<str:task_id>/', views.download_h5p_file, name='download_h5p_file'),
]
