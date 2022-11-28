from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from django.forms.models import model_to_dict
from .contractcalls import create_certificate, deploy_contract
from .models import Admin, User
from .contract_config import config
from .storagecalls import get_metadata_url, get_all_nfts, upload_image, add_frame


BASE_URL = "http://localhost:8000"


def home_page(request):
    return render(request, "index.html")


@api_view(["POST", "GET"])
def admin(request):
    try:
        account = request.data["account"]
        new_admin_account = request.data["new_admin_account"]
        name = request.data["name"]
        designation = request.data["designation"]
        if Admin.objects.filter(account=new_admin_account).exists():
            return Response({"status": "Failed", "response": "Admin already exists"})
        else:
            Admin.objects.create(
                name=name,
                designation=designation,
                account=new_admin_account,
                added_by=account,
            )
            return Response({"status": "Success", "response": "Admin added"})
    except:
        pass
    try:
        account = request.data["account"]
        if Admin.objects.filter(account=account).exists():
            admin = Admin.objects.get(account=account)
            admin_model = model_to_dict(admin)
            return Response({"status": "Success", "response": admin_model})
        else:
            return Response({"status": "Failed", "response": "Admin not found"})
    except:
        return Response({"status": "Failed", "response": "Admin is required"})


user_self_keys = [
    "name",
    "description",
    "website",
    "email",
    "contact",
    "regId",
    "idProof",
    "total_certificates",
    "total_souvenirs",
    "frames",
    "certificates",
    "storage_used",
]
user_admin_keys = [
    "comment",
    "status",
    "contract_address",
    "storage_limit",
    "nft_quota",
]


@api_view(["POST", "GET"])
def user(request):
    try:
        account = request.data["account"]
    except:
        return Response({"status": "Failed", "response": "Account is required"})
    try:
        querry_all = request.data["querry_all"]
        if Admin.objects.filter(account=account).exists():
            all_users = list(User.objects.all())
            all_users_sorted = []
            for user in all_users:
                print("---------------------------------------------------------------------")
                print(user)
                print(user.frames)
                user_model = model_to_dict(user)
                try:
                    user_model["idProof"] = BASE_URL + user_model["idProof"].url
                except:
                    user_model["idProof"] = ""
                all_users_sorted.append(user_model)
            return Response({"status": "Success", "response": all_users_sorted})
        else:
            return Response({"status": "Failed", "response": "Admin not found"})
    except:
        pass
    if not User.objects.filter(account=request.data["account"]).exists():
        User.objects.create(account=account)
    user = User.objects.get(account=account)
    for item in request.data.keys():
        if item in user_self_keys:
            if item == "frames":
                frame_url = upload_image(request.data["file"])
                frame_name = request.data["frame_name"]
                user.frames[frame_name] = frame_url
            else:
                setattr(user, item, request.data[item])
            if item == "regId":
                user.status = "in_progress"
        elif item in user_admin_keys:
            try:
                if Admin.objects.filter(account=request.data["admin"]).exists():
                    setattr(user, item, request.data[item])
                    if request.data[item] == "Approved":
                        contract_address = deploy_contract(user.name)
                        user.contract_address = contract_address
                else:
                    return Response({"status": "Failed", "response": "Admin not found"})
            except:
                return Response({"status": "Failed", "response": "Admin is required"})
    user.save()
    user_model = model_to_dict(user)
    try:
        user_model["idProof"] = BASE_URL + user_model["idProof"].url
    except:
        user_model["idProof"] = ""
    return Response({"status": "Success", "response": user_model})


@api_view(["POST", "GET"])
def kpi(request):
    certificates = 0
    souvenirs = 0
    users = User.objects.all()
    for user in users:
        certificates = certificates + user.total_certificates
        souvenirs = souvenirs + user.total_souvenirs
    return Response(
        {
            "status": "Success",
            "response": {"certificates": certificates, "souvenirs": souvenirs},
        }
    )


@api_view(["POST", "GET"])
def nft(request):
    if "frame" in request.data.keys():
        try:
            return mint_souvenir(request)
        except:
            return Response({"status": "Failed"})
    elif "image" in request.data.keys():
        try:
            return mint_individual_nft(request)
        except:
            return Response({"status": "Failed"})
    else:
        try:
            return get_nfts(request)
        except:
            return Response({"status": "Failed"})


def mint_individual_nft(request):
    account = request.data["account"]
    image = request.data["image"]
    asset_name = request.data["asset_name"]
    asset_description = request.data["asset_description"]
    user = User.objects.get(account=account)
    image_size = image.size / 1024 / 1024
    if user.storage_used + image_size <= user.storage_limit:
        contract_address = config["contract_address"]
        metadata_url = get_metadata_url(
            asset_name=asset_name, asset_description=asset_description, image=image
        )
        tx_hash = create_certificate(
            account=user.account,
            metadata=metadata_url,
            contract_address=contract_address,
        )
        user.storage_used = user.storage_used + image_size
        user.save()
        return Response({"status": "Success", "response": tx_hash})
    else:
        return Response({"status": "Failed", "response": "Storage quota exceeded."})


def get_nfts(request):
    nfts = get_all_nfts(request.data["account"])
    return Response({"status": "Success", "response": nfts})


def mint_souvenir(request):
    print("-----------------------------------------------------")
    account = request.data["account"]
    image = request.data["image"]
    asset_name = request.data["asset_name"]
    asset_description = request.data["asset_description"]
    recipient = request.data["recipient"]
    frame = request.data["frame"]
    if frame == "":
        framed_image = image
    else:
        framed_image = add_frame(image, frame)
    user = User.objects.get(account=account)
    contract_address = user.contract_address
    metadata_url = get_metadata_url(
        asset_name=asset_name, asset_description=asset_description, image=framed_image
    )
    tx_hash = create_certificate(
        account=recipient,
        metadata=metadata_url,
        contract_address=contract_address,
    )
    user.total_souvenirs = user.total_souvenirs + 1
    user.save()
    return Response({"status": "Success", "response": "tx_hash"})
