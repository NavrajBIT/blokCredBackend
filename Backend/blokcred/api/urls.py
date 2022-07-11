from django.urls import path
from . import views

urlpatterns = [
    path("individualfileupload", views.get_data),
    path("getcertificates", views.get_certificates),
    path("generatecertificate", views.generate_certificate),
]
