from django.urls import path
from . import views

urlpatterns = [
    # path("", views.home_page),
    path("admin", views.admin),
    path("user", views.user),
    path("kpi", views.kpi),
    path("nft", views.nft),
    path("verify", views.verify_cert),
    path("issueNftreward",views.mint_reward_nft),
    path("updatenft",views.update_reward_nft),
    path("viewnft",views.view_dnft_reward),
    path("claimreward",views.claim_reward),
    
]
