from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_page),
    path("admin", views.admin),
    path("user", views.user),
    path("kpi", views.kpi),
    path("nft", views.nft),
    path("verify", views.verify_cert),
]
