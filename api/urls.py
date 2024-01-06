from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_page),
    path("admin", views.admin),
    path("user", views.user),
    path("kpi", views.kpi),
    path("nft", views.nft),
    path("verify", views.verify_cert),
    path("certificate", views.cert_template),
    path("issue", views.issue_certificates),
    path("approval", views.approve_order),
    path("payment", views.payment),
    path("paypalpayment", views.paypal_payment),
    path("promocode", views.promocode),
    path("tryforfree", views.tryforfree),
    path("nonEssCert", views.issue_nonEsseCert),
    path("subForDev", views.customSubscriptionForDev),
    path("dnft", views.create_batch),
    path("latinCerts", views.add_dnfts),
    path("loyaltyNFT",views.mint_reward_nft),
    path("getOrderlist",views.getOrderList),
    path("retryCert",views.retry_certificate),
]
