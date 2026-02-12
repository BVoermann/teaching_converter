from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_pdf, name='upload_pdf'),
    path('progress/<str:task_id>/', views.check_progress, name='check_progress'),
    path('download/<str:task_id>/', views.download_file, name='download_file'),
    path('images-to-h5p/', views.upload_images_to_h5p, name='upload_images_to_h5p'),
    path('h5p-progress/<str:task_id>/', views.check_h5p_progress, name='check_h5p_progress'),
    path('h5p-download/<str:task_id>/', views.download_h5p_file, name='download_h5p_file'),
    path('compress-files/', views.upload_compress, name='upload_compress'),
    path('compress-progress/<str:task_id>/', views.check_compress_progress, name='check_compress_progress'),
    path('compress-download/<str:task_id>/', views.download_compress_file, name='download_compress_file'),
    path('pdf-to-images/', views.upload_pdf_images, name='upload_pdf_images'),
    path('pdf-images-progress/<str:task_id>/', views.check_pdf_images_progress, name='check_pdf_images_progress'),
    path('pdf-images-download/<str:task_id>/', views.download_pdf_images_file, name='download_pdf_images_file'),
]
