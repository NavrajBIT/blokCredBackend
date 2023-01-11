from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from django.forms.models import model_to_dict
from .contractcalls import (
    create_certificate,
    deploy_contract,
    get_token_id,
    get_contract_details,
)
from .models import Admin, User
from .contract_config import config
from .storagecalls import get_metadata_url, get_all_nfts, upload_image, add_frame
from web3 import Web3
import json
from django.core.files.storage import default_storage
from PIL import Image, ImageDraw, ImageFont
import qrcode
from django.conf import settings
from pathlib import Path
import requests


BASE_DIR = settings.BASE_DIR
BASE_URL = "http://localhost:8000"


def home_page(request):
    return render(request, "index.html")


@api_view(["POST", "GET"])
def admin(request):
    try:
        account = request.data["account"]
        new_admin_account = Web3.toChecksumAddress(request.data["new_admin_account"])
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
        account = Web3.toChecksumAddress(request.data["account"])
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
        account = Web3.toChecksumAddress(request.data["account"])
    except:
        return Response({"status": "Failed", "response": "Account is required"})
    try:
        querry_all = request.data["querry_all"]
        if Admin.objects.filter(account=account).exists():
            all_users = list(User.objects.all())
            all_users_sorted = []
            for user in all_users:
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
    if not User.objects.filter(account=account).exists():
        User.objects.create(account=account)
    user = User.objects.get(account=account)
    for item in request.data.keys():
        if item in user_self_keys:
            if item == "frames":
                try:
                    frame_url = save_frame(image=request.data["file"], user=user)
                    frame_name = request.data["frame_name"]
                    user.frames[frame_name] = frame_url
                except:
                    frame_name = request.data["frame_name"]
                    frames = user.frames
                    del frames[frame_name]
                    user.frames = frames
                    print(user.frames)
            elif item == "certificates":
                save_certificate_templates(user, request)
            else:
                setattr(user, item, request.data[item])
            if item == "regId":
                user.status = "in_progress"
        elif item in user_admin_keys:
            try:
                admin = request.data["admin"]
                if Admin.objects.filter(account=admin).exists():
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


def save_certificate_templates(user, request):
    user_certificates = user.certificates
    if "delete_certificate" in request.data.keys():
        print("deleting certificate")
        certificates = user.certificates
        certificate_name = request.data["template"]
        del certificates[certificate_name]
        user.certificates = certificates
        user.save()
        return None
    certificates = json.loads(request.data["certificates"])
    user_certificates[certificates["name"]] = {}
    for key in certificates.keys():
        if type(certificates[key]) is dict:
            file = request.data[key]
            filepath = (
                user.account
                + "/certificates/"
                + certificates["name"]
                + "/"
                + key
                + "/"
                + file.name
            )
            filename = default_storage.save(filepath, file)
            user_certificates[certificates["name"]][key] = filename
        else:
            user_certificates[certificates["name"]][key] = certificates[key]
    user.certificates = user_certificates
    user.save()


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
        except Exception as e:
            print(e)
            return Response({"status": "Failed"})
    elif "image" in request.data.keys():
        try:
            return mint_individual_nft(request)
        except Exception as e:
            print(e)
            return Response({"status": "Failed"})
    elif "cert" in request.data.keys():
        try:
            return mint_certificate(request=request)
        except Exception as e:
            print(e)
            return Response({"status": "Failed"})
    elif "all_certs" in request.data.keys():
        try:
            print("Minting bulk certs")
            return mint_bulk_certificate(request=request)
        except Exception as e:
            print(e)
            return Response({"status": "Failed"})
    else:
        try:
            return get_nfts(request)
        except:
            return Response({"status": "Failed"})


def mint_individual_nft(request):
    account = Web3.toChecksumAddress(request.data["account"])
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
    account = Web3.toChecksumAddress(request.data["account"])
    nfts = get_all_nfts(account)
    return Response({"status": "Success", "response": nfts})


def mint_souvenir(request):
    account = Web3.toChecksumAddress(request.data["account"])
    image = request.data["image"]
    asset_name = request.data["asset_name"]
    asset_description = request.data["asset_description"]
    recipient = Web3.toChecksumAddress(request.data["recipient"])
    frame = request.data["frame"]
    user = User.objects.get(account=account)
    if frame == "":
        framed_image = image
    else:
        framed_image = add_frame(base_image=image, frame_name=frame, user=user)
    contract_address = user.contract_address
    metadata_url = save_souvenir(
        asset_name=asset_name, asset_description=asset_description, image=framed_image, user=user
    )
    tx_hash = create_certificate(
        account=recipient,
        metadata=metadata_url,
        contract_address=contract_address,
    )
    user.total_souvenirs = user.total_souvenirs + 1
    user.save()
    return Response({"status": "Success", "response": "tx_hash"})


def mint_certificate(request):
    variable1 = request.data["variable1"]
    variable2 = request.data["variable2"]
    account = Web3.toChecksumAddress(request.data["account"])
    user = User.objects.get(account=account)
    template = request.data["template"]
    request_type = request.data["cert"]
    if request_type == "download":
        token_id = "000"
    elif request_type == "issue":
        token_id = str(get_token_id(user.contract_address))
    create_certificate_image(
        user=user,
        template=template,
        variable1=variable1,
        variable2=variable2,
        token_id=token_id,
    )
    download_filepath = (
        str(BASE_URL)
        + "/media/"
        + user.account
        + "/printed_certificates/"
        + template
        + "/"
        + user.contract_address
        + "/"
        + token_id
        + ".png"
    )
    if request_type == "download":
        return Response({"status": "Success", "response": download_filepath})
    elif request_type == "issue":
        recipient = Web3.toChecksumAddress(request.data["recipient"])
        metadata_url = (
            str(BASE_URL)
            + "/media/"
            + user.account
            + "/printed_certificates/"
            + template
            + "/"
            + user.contract_address
            + "/"
            + token_id
            + ".json"
        )
        tx_hash = create_certificate(
            account=recipient,
            metadata=metadata_url,
            contract_address=user.contract_address,
        )
        user.total_certificates = user.total_certificates + 1
        user.save()
        return Response({"status": "Success"})
    else:
        return Response({"status": "Failed", "response": "Invalid request type"})


def mint_bulk_certificate(request):
    account = Web3.toChecksumAddress(request.data["account"])
    user = User.objects.get(account=account)
    template = request.data["template"]
    all_certs = json.loads(request.data["all_certs"])
    response_data = []
    for cert in all_certs:
        try:
            variable1 = cert["variable1"]
            variable2 = cert["variable2"]
            recipient = cert["address"]
            token_id = str(get_token_id(user.contract_address))
            create_certificate_image(
                user=user,
                template=template,
                variable1=variable1,
                variable2=variable2,
                token_id=token_id,
            )
            recipient = Web3.toChecksumAddress(recipient)
            metadata_url = (
                str(BASE_URL)
                + "/media/"
                + user.account
                + "/printed_certificates/"
                + template
                + "/"
                + user.contract_address
                + "/"
                + token_id
                + ".json"
            )
            tx_hash = create_certificate(
                account=recipient,
                metadata=metadata_url,
                contract_address=user.contract_address,
            )
            user.total_certificates = user.total_certificates + 1
            user.save()
            download_filepath = (
                str(BASE_URL)
                + "/media/"
                + user.account
                + "/printed_certificates/"
                + template
                + "/"
                + user.contract_address
                + "/"
                + token_id
                + ".png"
            )
            response_data.append(
                {
                    "recipient": recipient,
                    "token_id": token_id,
                    "status": "Success",
                    "image": download_filepath,
                }
            )
        except:
            response_data.append({"recipient": recipient, "status": "Failed"})
    return Response({"status": "Success", "response": response_data})


def create_certificate_image(user, template, variable1, variable2, token_id):
    certificate = user.certificates[template]
    new_cert = Image.new(mode="RGB", size=(1080, 720), color=certificate["certColor"])
    cert = ImageDraw.Draw(new_cert)
    base_font_size = 9
    cert_text_data = [
        {"text": certificate["text1"], "font_size": 5, "y_coord": 50},
        {"text": certificate["text2"], "font_size": 2, "y_coord": 100},
        {"text": certificate["text3"], "font_size": 2, "y_coord": 170},
        {"text": variable1, "font_size": 5, "y_coord": 190},
        {"text": certificate["text4"], "font_size": 2, "y_coord": 255},
        {"text": variable2, "font_size": 2, "y_coord": 280},
        {"text": certificate["text5"], "font_size": 2, "y_coord": 320},
        {"text": certificate["text6"], "font_size": 2, "y_coord": 340},
        {"text": certificate["text7"], "font_size": 2, "y_coord": 360},
        {"text": certificate["text8"], "font_size": 2, "y_coord": 400},
        {"text": certificate["text9"], "font_size": 2, "y_coord": 420},
        {"text": certificate["text10"], "font_size": 2, "y_coord": 440},
        {"text": certificate["signtext2"], "font_size": 2, "y_coord": 680},
    ]
    print("here")
    for text in cert_text_data:
        x, y, w, h = cert.textbbox(
            (0, 0),
            text["text"],
            font=ImageFont.truetype(
                "arial.ttf", int(base_font_size * text["font_size"])
            ),
        )
        cert.text(
            ((1080 - w) / 2, text["y_coord"]),
            text["text"],
            fill=certificate["fontColor"],
            font=ImageFont.truetype(
                "arial.ttf", int(base_font_size * text["font_size"])
            ),
        )
    x, y, w, h = cert.textbbox(
        (0, 0),
        certificate["signtext1"],
        font=ImageFont.truetype("arial.ttf", int(base_font_size * 2)),
    )
    cert.text(
        (10 + (216 - w) / 2, 680),
        certificate["signtext1"],
        fill=certificate["fontColor"],
        font=ImageFont.truetype("arial.ttf", int(base_font_size * 2)),
    )
    x, y, w, h = cert.textbbox(
        (0, 0),
        certificate["signtext3"],
        font=ImageFont.truetype("arial.ttf", int(base_font_size * 2)),
    )
    cert.text(
        (1070 - 216 + (216 - w) / 2, 680),
        certificate["signtext3"],
        fill=certificate["fontColor"],
        font=ImageFont.truetype("arial.ttf", int(base_font_size * 2)),
    )

    cert.text(
        (560, 480),
        "Contract:",
        fill=certificate["fontColor"],
        font=ImageFont.truetype("arial.ttf", int(base_font_size * 1.5)),
    )
    cert.text(
        (620, 480),
        user.contract_address,
        fill=certificate["fontColor"],
        font=ImageFont.truetype("arial.ttf", int(base_font_size * 1.5)),
    )
    cert.text(
        (560, 500),
        "Token Id:",
        fill=certificate["fontColor"],
        font=ImageFont.truetype("arial.ttf", int(base_font_size * 1.5)),
    )
    cert.text(
        (620, 500),
        token_id,
        fill=certificate["fontColor"],
        font=ImageFont.truetype("arial.ttf", int(base_font_size * 1.5)),
    )
    cert.text(
        (560, 520),
        "Chain Id:",
        fill=certificate["fontColor"],
        font=ImageFont.truetype("arial.ttf", int(base_font_size * 1.5)),
    )
    cert.text(
        (620, 520),
        "137",
        fill=certificate["fontColor"],
        font=ImageFont.truetype("arial.ttf", int(base_font_size * 1.5)),
    )
    qr = qrcode.QRCode(box_size=3)
    qr_data = "https://bitmemoir.com/verify/" + user.contract_address + "/" + token_id
    qr.add_data(qr_data)
    qr.make()
    qr_image = qr.make_image(
        fill_color=certificate["fontColor"], back_color=certificate["certColor"]
    )
    new_cert.paste(qr_image, (420, 470))
    try:
        filepath = str(BASE_DIR) + "/media/" + certificate["logo1"]
        img = Image.open(filepath)
        img = img.resize((162, 108))
        new_cert.paste(img, (10, 10), img)
    except:
        pass
    try:
        filepath = str(BASE_DIR) + "/media/" + certificate["logo2"]
        img = Image.open(filepath)
        img = img.resize((162, 108))
        new_cert.paste(img, (908, 10), img)
    except:
        pass
    try:
        filepath = str(BASE_DIR) + "/media/" + certificate["sign1"]
        img = Image.open(filepath)
        img = img.resize((216, 76))
        new_cert.paste(img, (10, 600), img)
    except:
        pass
    try:
        filepath = str(BASE_DIR) + "/media/" + certificate["sign2"]
        img = Image.open(filepath)
        img = img.resize((216, 76))
        new_cert.paste(img, (432, 600), img)
    except:
        pass
    try:
        filepath = str(BASE_DIR) + "/media/" + certificate["sign3"]
        img = Image.open(filepath)
        img = img.resize((216, 76))
        new_cert.paste(img, (854, 600), img)
    except:
        pass
    dir_path = (
        str(BASE_DIR)
        + "/media/"
        + user.account
        + "/printed_certificates/"
        + template
        + "/"
        + user.contract_address
    )    
    filepath = dir_path + "/" + token_id + ".png"
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    new_cert.save(filepath)
    download_filepath = (
        str(BASE_URL)
        + "/media/"
        + user.account
        + "/printed_certificates/"
        + template
        + "/"
        + user.contract_address
        + "/"
        + token_id
        + ".png"
    )
    metadata_filepath = dir_path + "/" + token_id + ".json"
    description = ""
    for text in cert_text_data:
        if cert_text_data.index(text) <= 11:
            description = description + " " + text["text"]
    metadata = {
        "name": user.name,
        "description": description,
        "image": download_filepath,
    }
    if certificate["variable1"] != "":
        metadata[certificate["variable1"]] = variable1
    if certificate["variable2"] != "":
        metadata[certificate["variable2"]] = variable2
    with open(metadata_filepath, "w") as metadata_file:
        json.dump(metadata, metadata_file)


def save_frame(image, user):
    dir_path = str(BASE_DIR) + "/media/" + user.account + "/frames/"
    filepath = dir_path + image.name
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    frame = Image.open(image)
    frame.save(filepath)
    download_filepath = (
        str(BASE_URL) + "/media/" + user.account + "/frames/" + image.name
    )
    return download_filepath

def save_souvenir(image, user, asset_name, asset_description):
    print("Saving souvenir")
    dir_path = str(BASE_DIR) + "/media/" + user.account + "/souvenirs/"
    filepath = dir_path + asset_name + ".png"
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    # souvenir = Image.open(image)
    souvenir = image
    souvenir.show()
    souvenir.save(filepath)
    download_filepath = (
        str(BASE_URL) + "/media/" + user.account + "/souvenirs/" + asset_name + ".png"
    )
    metadata = {
        "name": asset_name,
        "description": asset_description,
        "image": download_filepath,
    }
    metadata_filepath = dir_path + asset_name + ".json"
    with open(metadata_filepath, "w") as metadata_file:
        json.dump(metadata, metadata_file)
    metadata_url = (
        str(BASE_URL) + "/media/" + user.account + "/souvenirs/" + asset_name + ".json"
    )
    print(metadata_url)
    return metadata_url


@api_view(["POST", "GET"])
def verify_cert(request):
    contract_address = request.data["contract_address"]
    token_id = request.data["token_id"]
    try:
        owner, metadata_uri = get_contract_details(
            contract_address=contract_address, token_id=token_id
        )
    except Exception as e:
        print(e)
        return Response({"status": "Success", "response": "Invalid data."})
    is_verified = False
    if User.objects.filter(contract_address=contract_address).exists():
        user = User.objects.get(contract_address=contract_address)
        is_verified = user.status == "Approved"
        user_data = {
            "name": user.name,
            "description": user.description,
            "account": user.account,
        }
        nft_data = {
            "owner": owner,
            "metadata_uri": metadata_uri,
        }
    if is_verified:
        response = requests.get(url=metadata_uri, stream=True)
        metadata = response.json()
        for trait in metadata.keys():
            if trait != "name" and trait != "description":
                nft_data[trait] = metadata[trait]
        return Response(
            {
                "status": "Success",
                "response": {
                    "user_data": user_data,
                    "nft_data": nft_data,
                },
            }
        )
