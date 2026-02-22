from django.urls import path
from . import views

urlpatterns = [
    path('download/<str:course_name>/', views.download_certificate, name='download_certificate'),
]