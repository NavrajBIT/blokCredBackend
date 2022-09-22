from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_page),
    path("addAdmin", views.add_admin),
    path("checkAdmin", views.check_admin),
    path("getNumberOfCertificates", views.get_certs),
    path("addIssuer", views.add_issuer),
    path("addDestination", views.add_destination),
    path("checkDestination", views.check_destination),
    path("getIndividual", views.get_individual),
    path("individualfileupload", views.file_upload),
    path("createSouvenir", views.create_souvenir_image),
    path("addSouvenir", views.souvenir_upload),
    path("getcertificates", views.get_certificates),
    path("getIssuerDetails", views.get_issuer),
    path("eocerts", views.issue_eo_certs),
]
