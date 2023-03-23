from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from django.forms.models import model_to_dict
from .contractcalls import (
    create_certificate,   
    deploy_contract,
    get_token_id,
    get_contract_details,
    check_payment
)
from .models import (
    Admin,
    User,
    Template,
    Template_Variable,
    Certificate_Order,
    Certificate,
    Approver,
    Approval_OTP,
    Subscription,
)
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
from django.core.mail import send_mail, EmailMessage
import csv
from io import StringIO
import random
import ast
# datetime
from datetime import datetime, timedelta,date
import pytz
import os

utc=pytz.UTC

from django.utils import timezone
from django.core import serializers
from django.http import JsonResponse

BASE_DIR = settings.BASE_DIR
BASE_URL = "http://localhost:8000"
# FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_PATH='arial.ttf'



def home_page(request):
    try:
        Admin.objects.create(
            name="Hemant",
            designation="Developer",
            account=Web3.toChecksumAddress(
                "0xcebFD12bA1e85a797BFdf62081785E9103A96Dd3"
            ),
            added_by=Web3.toChecksumAddress(
                "0xE858f0370b101cD3F58E03F18BFA1240a591b5Fa"
            ),
        )
    except Exception as e:
        print(e)
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
    "approvers",
    "issuerName",
    "issuerDesignation",
    "country",
    "noteSignByHigherAuth"
    
    
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
                    user_model["noteSignByHigherAuth"] = BASE_URL + user_model["noteSignByHigherAuth"].url
                except:
                    user_model["idProof"] = ""
                    user_model["noteSignByHigherAuth"] =""
                approvers = []
                for approver in user.approvers.all():
                    approver_model = model_to_dict(approver)
                    approver_model["idProofApprover"] = BASE_URL + approver_model["idProofApprover"].url
                    approvers.append(approver_model)
                user_model["approvers"] = approvers
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
            elif item == "approvers":
                user.approvers.clear()
                approvers = json.loads(request.data["approvers"])            
                print(approvers)   
                for approver in approvers:
                    num=1
                    new_approver = Approver.objects.create(
                        name=approver["name"],
                        designation=approver["designation"],
                        email=approver["email"],
                        idProofApprover=request.data[f"idProofApprovers{num}"],
                    )
                    user.approvers.add(new_approver)
                    num+=1

                # new_approver = Approver.objects.create(
                #     name=approvers[0]["name"],
                #     designation=approvers[0]["designation"],
                #     email=approvers[0]["email"],
                #     idProofApprover=idproofAp,
                #     signNoteApprover=signId,
                # )
                # user.approvers.add(new_approver)
                    
            else:
                setattr(user, item, request.data[item])
            if item == "regId":
                user.status = "in_progress"
        elif item in user_admin_keys:
            try:
                admin = Web3.toChecksumAddress(request.data["admin"])
                if Admin.objects.filter(account=admin).exists():
                    setattr(user, item, request.data[item])
                    if request.data[item] == "Approved":
                        contract_address = deploy_contract(user.name)
                        user.contract_address = contract_address
                else:
                    return Response({"status": "Failed", "response": "Admin not found"})
            except Exception as e:
                print(e)
                return Response({"status": "Failed", "response": "Admin is required"})
    user.save()
    user_model = model_to_dict(user)
    try:
        user_model["idProof"] = BASE_URL + user_model["idProof"].url
        user_model["noteSignByHigherAuth"] = BASE_URL + user_model["noteSignByHigherAuth"].url
        subsDetails= Subscription.objects.get(
        id=user_model["subscription"]
        )
        subsDetails=model_to_dict(subsDetails)
        user_model["subscription"]=subsDetails
    except:
        user_model["idProof"] = ""
        user_model["noteSignByHigherAuth"] =""
        user_model["subscription"]=""
    approvers = []
    for approver in user.approvers.all():
        approver_model = model_to_dict(approver)
        approver_model["idProofApprover"] = BASE_URL + approver_model["idProofApprover"].url
        approvers.append(approver_model)
    user_model["approvers"] = approvers
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
        asset_name=asset_name,
        asset_description=asset_description,
        image=framed_image,
        user=user,
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
        try:
            email = request.data["email"]
            send_cert_email(
                recipient=email,
                file=filepath,
                recipient_name=variable1,
                sender_name=user.name,
            )
        except Exception as e:
            print(e)
            pass
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
            try:
                email = cert["email"]
                send_cert_email(
                    recipient=email,
                    file=filepath,
                    recipient_name=variable1,
                    sender_name=user.name,
                )
            except Exception as e:
                print(e)
                pass
            response_data.append(
                {
                    "recipient": recipient,
                    "token_id": token_id,
                    "status": "Success",
                    "image": download_filepath,
                }
            )

        except Exception as e:
            print(e)
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
                FONT_PATH, int(base_font_size * text["font_size"])
            ),
        )
        print("got till here.....")
        cert.text(
            ((1080 - w) / 2, text["y_coord"]),
            text["text"],
            fill=certificate["fontColor"],
            font=ImageFont.truetype(
                FONT_PATH, int(base_font_size * text["font_size"])
            ),
        )
    x, y, w, h = cert.textbbox(
        (0, 0),
        certificate["signtext1"],
        font=ImageFont.truetype(FONT_PATH, int(base_font_size * 2)),
    )
    cert.text(
        (10 + (216 - w) / 2, 680),
        certificate["signtext1"],
        fill=certificate["fontColor"],
        font=ImageFont.truetype(FONT_PATH, int(base_font_size * 2)),
    )
    x, y, w, h = cert.textbbox(
        (0, 0),
        certificate["signtext3"],
        font=ImageFont.truetype(FONT_PATH, int(base_font_size * 2)),
    )
    cert.text(
        (1070 - 216 + (216 - w) / 2, 680),
        certificate["signtext3"],
        fill=certificate["fontColor"],
        font=ImageFont.truetype(FONT_PATH, int(base_font_size * 2)),
    )

    cert.text(
        (560, 480),
        "Contract:",
        fill=certificate["fontColor"],
        font=ImageFont.truetype(FONT_PATH, int(base_font_size * 1.5)),
    )
    cert.text(
        (620, 480),
        user.contract_address,
        fill=certificate["fontColor"],
        font=ImageFont.truetype(FONT_PATH, int(base_font_size * 1.5)),
    )
    cert.text(
        (560, 500),
        "Token Id:",
        fill=certificate["fontColor"],
        font=ImageFont.truetype(FONT_PATH, int(base_font_size * 1.5)),
    )
    cert.text(
        (620, 500),
        token_id,
        fill=certificate["fontColor"],
        font=ImageFont.truetype(FONT_PATH, int(base_font_size * 1.5)),
    )
    cert.text(
        (560, 520),
        "Chain Id:",
        fill=certificate["fontColor"],
        font=ImageFont.truetype(FONT_PATH, int(base_font_size * 1.5)),
    )
    cert.text(
        (620, 520),
        "137",
        fill=certificate["fontColor"],
        font=ImageFont.truetype(FONT_PATH, int(base_font_size * 1.5)),
    )
    qr = qrcode.QRCode(box_size=3)
    print("adding qr code")
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
    print(dir_path)
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
    # souvenir.show()
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
    print(contract_address)
    print(token_id)
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


def send_cert_email(recipient, file, recipient_name, sender_name):
    subject = "Verified certificate recieved."
    message = (
        "Hi"
        + recipient_name
        + ",\nYou have recieved a verified certificate from "
        + sender_name
        + ". \n"
    )
    sender = "navraj@beimagine.tech"
    recipients = [recipient]
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=sender,
        to=recipients,
    )
    email.attach_file(file)
    email.send(fail_silently=False)

@api_view(["POST", "GET"])
def cert_template(request):
    request_type = request.data["request_type"]
    account = Web3.toChecksumAddress(request.data["account"])
    user = User.objects.get(account=account)
    if request_type == "create":
        sector = request.data["sector"]
        category = request.data["category"]
        subscription = request.data["subscription"]
        base_image = request.data["base_image"]
        name = request.data["name"]
        template = Template.objects.create(
            user=user,
            base_image=base_image,
            name=name,
            sector=sector,
            category=category,
            subscription=subscription,
        )
        variables = json.loads(request.data["variables"])
        for variable in variables:
            template_variable = Template_Variable.objects.create(
                name=variable["name"],
                x_pos=variable["x_pos"],
                width=variable["width"],
                height=variable["height"],
                color=variable["color"],
                y_pos=variable["y_pos"],
                type=variable["type"],
            )
            template.variables.add(template_variable)
            template.save()
        response_data = model_to_dict(template)
        response_data["base_image"] = BASE_URL + template.base_image.url
        response_variables = []
        for variable in template.variables.all():
            response_variables.append(model_to_dict(variable))
        response_data["variables"] = response_variables
        return Response(
            {
                "status": "Success",
                "response": response_data,
            }
        )
    elif request_type == "read":
        sector = request.data["sector"]
        category = request.data["category"]
        subscription = request.data["subscription"]
        from_index = int(request.data["from_index"])
        to_index = int(request.data["to_index"])
        if subscription == "user":
            print(user, sector, category, subscription)
            templates = Template.objects.filter(
                user=user,
                sector=sector,
                subscription=subscription,
            )[from_index:to_index]
            # templates= json.dumps(list(templates.values()))
        else:
            templates = Template.objects.filter(
                sector=sector,
                category=category,
                subscription=subscription,
            )
        templates_sorted = []
        for template in templates:
            my_template = model_to_dict(template)
            try:
                my_template["base_image"] = BASE_URL + template.base_image.url
            except:
                my_template["base_image"] = ""
            my_variables = []
            for variable in template.variables.all():
                my_variables.append(model_to_dict(variable))
            my_template["variables"] = my_variables
            templates_sorted.append(my_template)
        return Response(
            {
                "status": "Success",
                "response": templates_sorted,
            }
        )
    elif request_type == "delete":
        id = request.data["id"]
        Template.objects.get(pk=id).delete()
        return Response(
            {
                "status": "Success",
                "response": "done",
            }
        )


@api_view(["POST", "GET"])
def issue_certificates(request):
    server_url = request.META.get('HTTP_REFERER', '')
    account = Web3.toChecksumAddress(request.data["account"])
    user = User.objects.get(account=account)    
    subscription = Subscription.objects.get(user=user)
    template_id = request.data["template_id"]
    template = Template.objects.get(pk=template_id)
    file = request.data["file"]
    order = Certificate_Order.objects.create(user=user, template=template, file=file)
    file = order.file.read().decode("utf-8")
    csv_data = list(csv.reader(StringIO(file), delimiter=","))
    cert_no = len(csv_data) - 1
    if (cert_no >= user.nft_quota or subscription.end_Date <= timezone.now()):
        return Response(
            {
                "status": "Failed",
                "response": "Not enough balance/SUBSCRIPTION EXPIRED",
            }
        )
    else:
        user.nft_quota = user.nft_quota - cert_no
        user.save()
    variable_name_index = {}
    for index in enumerate(csv_data[0]):
        if index[0] != 0 and index[0] < len(csv_data[0]) - 2:
            variable_name_index[csv_data[0][index[0]]] = index[0]
    for s_no in range(1, len(csv_data)):
        variables = {}
        for variable in variable_name_index.keys():
            variables[variable] = csv_data[s_no][variable_name_index[variable]]        
        certificate = Certificate.objects.create(
            user=user,
            template=template,
            recipient=Web3.toChecksumAddress(csv_data[s_no][len(csv_data[0]) - 2]),
            email=csv_data[s_no][len(csv_data[0]) - 1],
            image_url="",
            metadata_url="",
            variable_values=variables
        )
        order.certificates.add(certificate)
        order.save()
    if len(list(user.approvers.all())) == 0:
        execute_certificate_order(order,server_url)
        return Response(
            {
                "status": "Success",
                "response": "issued",
            }
        )
    else:
        for approver in user.approvers.all():
            otp = int(random.random() * 1000000)
            approval = Approval_OTP.objects.create(
                approver=approver, order=order, otp=otp
            )
            send_cert_approval_email(approval)
        return Response(
            {
                "status": "Success",
                "response": "pending approval",
            }
        )

@api_view(["POST", "GET"])
def issue_nonEsseCert(request):
    server_url = request.META.get('HTTP_REFERER', '')
    print(server_url)
    account = Web3.toChecksumAddress(request.data["account"])
    user = User.objects.get(account=account)    
    subscription = Subscription.objects.get(user=user)
    template_id = request.data["template_id"]
    template = Template.objects.get(pk=template_id)
    file = request.data["file"]
    order = Certificate_Order.objects.create(user=user, template=template, file=file)
    file = order.file.read().decode("utf-8")
    csv_data = list(csv.reader(StringIO(file), delimiter=","))
    cert_no = len(csv_data) - 1
    if (cert_no >= user.nft_quota or subscription.end_Date <= timezone.now()):
        return Response(
            {
                "status": "Failed",
                "response": "Not enough balance/SUBSCRIPTION EXPIRED",
            }
        )
    else:
        user.nft_quota = user.nft_quota - cert_no
        user.save()
    variable_name_index = {}
    for index in enumerate(csv_data[0]):
        if index[0] != 0 and index[0] < len(csv_data[0]) - 2:
            variable_name_index[csv_data[0][index[0]]] = index[0]
    for s_no in range(1, len(csv_data)):
        variables = {}
        for variable in variable_name_index.keys():
            variables[variable] = csv_data[s_no][variable_name_index[variable]]        
        certificate = Certificate.objects.create(
            user=user,
            template=template,
            recipient=Web3.toChecksumAddress(csv_data[s_no][len(csv_data[0]) - 2]),
            email=csv_data[s_no][len(csv_data[0]) - 1],
            image_url="",
            metadata_url="",
            variable_values=variables
        )
        order.certificates.add(certificate)
        order.save()    
    execute_certificate_order(order,server_url)
    return Response(
        {
            "status": "Success",
            "response": "issued",
        }
    )

    
def create_certificate_from_template(certificate, token_id,server_url):
    print(token_id)
    template = certificate.template
    print(certificate.variable_values)
    variables = certificate.variable_values
    base_image = Image.open(template.base_image.path)
    width, height = base_image.size
    cert = ImageDraw.Draw(base_image)
    for variable in template.variables.all():
        text_box_width = variable.width * width / 100
        text_box_height = int(variable.height * height / 100)
        if variable.type == "text":
            text_box_pos_x = variable.x_pos * width / 100
            text_box_pos_y = variable.y_pos * height / 100 - text_box_height / 2
            x, y, w, h = cert.textbbox(
                (0, 0),
                variables[variable.name],
                font=ImageFont.truetype(FONT_PATH, text_box_height),
            )
            cert.text(
                (text_box_pos_x - w / 2, text_box_pos_y),
                variables[variable.name],
                fill=variable.color,
                font=ImageFont.truetype(FONT_PATH, text_box_height),
            ),
        elif variable.type == "qr":
            print("Image size =", height)
            print("QR size ", int(variable.height * height / 100))
            qr = qrcode.QRCode(version=None, box_size=3)
            qr_data = server_url+ "#/verify/" + template.user.contract_address + "/" + str(token_id)
            print(qr_data)
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_image = qr.make_image(
                    fill_color=variable.color, back_color=(255, 255, 255, 0)
            )
            qr_image = qr_image.resize((text_box_height, text_box_height))
            mask = qr_image.convert("L").point(lambda x: 255 - x)
            base_image.paste(qr_image, (int(variable.x_pos * width / 100), int(variable.y_pos * height / 100 - text_box_height / 2)), mask=mask)
    # base_image.show()
    root_dir = os.path.dirname(str(BASE_DIR) + "/media/" + certificate.user.account + "/certificates/")
    print(root_dir)
    root_url = os.path.dirname(str(BASE_URL) + "/media/" + certificate.user.account + "/certificates/")
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)
    image_location = str(root_dir) + "/" + str(certificate.id ) + ".png"
    image_url = str(root_url) + "/" + str(certificate.id )+ ".png"
    print(image_location, image_url)
    base_image.save(image_location)
    asset_name = " ".join([template.name, "Issued by", template.user.name])
    description = ""
    for variable in variables.keys():
        description = description + variable + ": " + variables[variable] + ",  "
    metadata = {
        "name": asset_name,
        "description": description,
        "image": image_url,
    }
    metadata_filepath = str(root_dir) + "/" + str(certificate.id )+ ".json"
    with open(metadata_filepath, "w") as metadata_file:
        json.dump(metadata, metadata_file)
    metadata_url = str(root_url) + "/" + str(certificate.id ) + ".json"   
    certificate.image_url = image_url
    certificate.metadata_url = metadata_url
    certificate.token_id = token_id
    certificate.save()
    return metadata_url

def execute_certificate_order(order,server_url):
    for certificate in order.certificates.all():  
        metadata_url = BASE_URL + "/media/" + certificate.user.account + "/certificates/" + str(certificate.id ) + ".json"
        token_id = create_certificate(
            account=certificate.recipient,
            metadata=metadata_url,
            contract_address=order.user.contract_address,
        )
        print(token_id)
        print(metadata_url)
        create_certificate_from_template(certificate=certificate, token_id=token_id,server_url=server_url)
    order.fulfilled = True
    order.save()


def send_cert_approval_email(approval):
    subject = "Certificate issuance approval request."
    greeting = "Hi " + approval.approver.name + ","
    first_line = "Your approval is required for certificate issuance."
    second_line = (
        "Certificate issuance has been initiated by "
        + str(approval.order.user.name)
        + " through BitMemoir."
    )
    third_line = "PFA the certificate data."
    fourth_line = "Click on the link below to approve."
    link = (
        "http://localhost:3000/#/approval/"
        + str(approval.order.id)
        + "/"
        + str(approval.otp)
    )
    fifth_line = "Kind Regards,"
    sixth_line = "Beyond Imagination Technologies."
    message = "\n\n".join(
        [
            greeting,
            first_line,
            second_line,
            third_line,
            fourth_line,
            link,
            fifth_line,
            sixth_line,
        ]
    )
    sender = "navraj@beimagine.tech"
    recipients = [approval.approver.email]
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=sender,
        to=recipients,
    )
    # email.attach_file(file)
    email.send(fail_silently=False)


@api_view(["POST", "GET"])
def approve_order(request):
    order_id = int(request.data["order_id"])
    order = Certificate_Order.objects.get(pk=order_id)
    otp = int(request.data["otp"])
    approval = Approval_OTP.objects.get(order=order, otp=otp)
    approval.approved = True
    approval.save()
    if Approval_OTP.objects.filter(order=order, approved=False).exists():
        all_approvals = Approval_OTP.objects.filter(order=order, approved=False)
        approvers = []
        for approval in all_approvals:
            approver=model_to_dict(approval.approver)
            approver['idProofApprover']=""
            approvers.append(approver)
        return Response(
            {
                "status": "Success",
                "response": approvers,
            }
        )
    else:
        if not order.fulfilled:
            execute_certificate_order(order)
        return Response(
            {
                "status": "Success",
                "response": "Fulfilled",
            }
        )
        

@api_view(["POST", "GET"])
def payment(request):
    tx_hash = request.data["tx_hash"]
    plan = request.data["plan"]
    duration_days = int(request.data["duration_days"])
    start_Date = date.today()
    end_Date = start_Date+timedelta(days=duration_days)
    amount, user_address = check_payment(tx_hash)
    if amount > 0:
        user = User.objects.get(account=Web3.toChecksumAddress(user_address))
        if amount >= 1000:
            user.nft_quota = user.nft_quota + 1000
            # user.save()
            subs=Subscription.objects.create(
                plan=plan, duration_days=duration_days,
                start_Date=start_Date, end_Date=end_Date)
            user.subscription =  subs
            user.save()
    return Response(
        {
            "status": "Success",
            "response": "Fulfilled",
        }
    )  
        
@api_view(["POST", "GET"])
def customSubscriptionForDev(request):
        # tx_hash = request.data["tx_hash"]
    plan = request.data["plan"]
    duration_days = int(request.data["duration_days"])
    start_Date = date.today()
    end_Date = start_Date+timedelta(days=duration_days)
    # amount, user_address = check_payment(tx_hash)
    user_address = request.data["user_address"]
    print(user_address)
    print(plan)
    print(duration_days)
    amount = 1000
    if amount > 0:
        user = User.objects.get(account=Web3.toChecksumAddress(user_address))
        if amount >= 1000:
            user.nft_quota = user.nft_quota + 1000
            # user.save()
            subs=Subscription.objects.create(
                user=user,plan=plan, duration_days=duration_days,
                start_Date=start_Date, end_Date=end_Date)
            print(subs)
            user.subscription =  subs
            user.save()
    return Response(
        {
            "status": "Success",
            "response": "Fulfilled",
        }
    )  
        
