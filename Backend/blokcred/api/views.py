from urllib import response
from rest_framework.response import Response
from rest_framework.decorators import api_view
import requests
import ipfsApi
from .image_creator import create_image
# from .generateCredentials import generatePassword
from .contractcalls import create_certificate, deploy_contract, create_souvenir
from .models import nft, admin, issuer, destination, kpi, individual
from .serializers import nft_serializer
from django.forms.models import model_to_dict
from .souvenir_creator import add_souvenir_frame
from django.http import HttpResponse
import os
from .eocerts import issuecertificates


# Add admin
@api_view(["POST"])
def add_admin(request):
    account = request.data["account"]
    name = request.data['name']
    designation = request.data['designation']
    added_by = request.data['addedBy']
    if admin.objects.filter(account=added_by).exists():
        if admin.objects.filter(account=account).exists():
            existing_admin = admin.objects.filter(account=account).first()
            existing_admin.name = name
            existing_admin.designation = designation
            existing_admin.added_by = added_by
            existing_admin.save()
        else:
            admin.objects.create(
                name=name,
                designation=designation,
                account=account,
                added_by=added_by
            )
        return Response({"status": "Success"})
    else:
        return Response({"status": "Failed", "response": "Only admin can add new admin."})

# Check if this is the admin


@api_view(["POST"])
def check_admin(request):
    account = request.data["account"]
    if admin.objects.filter(account=account).exists():
        admin_model = admin.objects.filter(account=account).first()
        admin_data = model_to_dict(admin_model)
        return Response({"status": "Success", "credentials": admin_data})
    return Response({"status": "Failed"})


@api_view(["GET"])
def get_certs(request):
    print(request)
    if kpi.objects.filter(id=1).exists():
        kpi_model = kpi.objects.filter(id=1).first()
    else:
        kpi.objects.create(id=1, total_certificates=0)
        kpi_model = kpi.objects.filter(id=1).first()
    kpi_data = model_to_dict(kpi_model)
    return Response({"status": "Success", "credentials": kpi_data})


# Add issuer
@api_view(["POST"])
def add_issuer(request):
    account = request.data["account"]
    name = request.data['name']
    description = request.data['description']
    added_by = request.data['addedBy']
    if admin.objects.filter(account=added_by).exists():
        if issuer.objects.filter(account=account).exists():
            existing_issuer = issuer.objects.filter(account=account).first()
            existing_issuer.name = name
            existing_issuer.description = description
            existing_issuer.added_by = added_by
            existing_issuer.save()
        else:
            contract_address = deploy_contract(name)
            issuer.objects.create(
                name=name,
                description=description,
                account=account,
                added_by=added_by,
                contract_address=contract_address
            )
        return Response({"status": "Success"})
    else:
        return Response({"status": "Failed", "response": "Only admin can add new issuer."})


# Check if this is the issuer
@api_view(["POST"])
def check_issuer(request):
    account = request.data["account"]
    if issuer.objects.filter(account=account).exists():
        issuer_model = issuer.objects.filter(account=account).first()
        issuer_data = model_to_dict(issuer_model)
        return Response({"status": "Success", "credentials": issuer_data})
    return Response({"status": "Failed"})

# Get issuer details


@api_view(["POST"])
def get_issuer(request):
    account = request.data["address"]
    if issuer.objects.filter(account=account).exists():
        issuer_model = issuer.objects.filter(account=account).first()
        issuer_data = model_to_dict(issuer_model)
        return Response({"status": "Success", "credentials": issuer_data})
    elif destination.objects.filter(account=account).exists():
        destination_model = destination.objects.filter(account=account).first()
        destination_data = model_to_dict(destination_model)
        return Response({"status": "Success", "credentials": destination_data})
    return Response({"status": "Failed"})


# Add destination
@api_view(["POST"])
def add_destination(request):
    print(request)
    account = request.data["account"]
    name = request.data['name']
    description = request.data['description']
    added_by = request.data['addedBy']
    frame = request.data['frame']
    if admin.objects.filter(account=added_by).exists():
        if destination.objects.filter(account=account).exists():
            existing_destination = destination.objects.filter(
                account=account).first()
            existing_destination.name = name
            existing_destination.description = description
            existing_destination.added_by = added_by
            existing_destination.frame = frame
            existing_destination.save()
        else:
            contract_address = deploy_contract(name)
            destination.objects.create(
                name=name,
                description=description,
                account=account,
                added_by=added_by,
                frame=frame,
                contract_address=contract_address
            )
        return Response({"status": "Success"})
    else:
        return Response({"status": "Failed", "response": "Only admin can add new destination."})


# Check if this is the issuer
@api_view(["POST"])
def check_destination(request):
    account = request.data["account"]
    if destination.objects.filter(account=account).exists():
        destination_model = destination.objects.filter(account=account).first()
        destination_data = model_to_dict(destination_model)
        print("destination found.")
        print(destination_data)
        return Response({"status": "Success", "credentials": destination_data})
    return Response({"status": "Failed"})


# Souvenir file upload to NFT
@api_view(["POST"])
def souvenir_upload(request):
    print(request.data)
    account = request.data["account"]
    name = request.data["name"]
    description = request.data["description"]
    metadataURL = request.data['metadata']
    imageURL = request.data['image']
    added_by = request.data['addedBy']
    this_destination = destination.objects.filter(account=added_by).first()
    contract_address = this_destination.contract_address
    if nft.objects.filter(metadata_url=metadataURL).exists():
        return Response({"status": "Already exists"})
    (token_id, tx_hash) = create_souvenir(
        account, metadataURL, contract_address=contract_address)
    response_object = {
        "status": "Success",
        "tokenId": token_id,
        "tx_hash": tx_hash,
    }
    print(response_object)
    nft.objects.create(owner=account,
                       name=name,
                       description=description,
                       token_id=token_id,
                       file_url=imageURL, metadata_url=metadataURL, is_live=True, is_verified=True, issuer=added_by)
    kpi_model = kpi.objects.filter(id=1).first()
    total_certificates = kpi_model.total_certificates + 1
    only_souvenirs = kpi_model.only_souvenirs + 1
    kpi_model.total_certificates = total_certificates
    kpi_model.only_souvenirs = only_souvenirs
    kpi_model.save()
    this_destination.total_certificates = this_destination.total_certificates + 1
    this_destination.save()
    return Response(response_object)


@api_view(["POST"])
def create_souvenir_image(request):
    image = request.data['image']
    frame_url = request.data['frame_url']
    souvenir_path = add_souvenir_frame(image, frame_url)
    with open(souvenir_path, "rb") as file:
        souvenir = file
        response = HttpResponse(souvenir.read(), content_type="image/png")
    os.remove(souvenir_path)
    return response


# Get individual details
@api_view(["POST"])
def get_individual(request):
    account = request.data["account"]
    if individual.objects.filter(account=account).exists():
        this_individual = individual.objects.filter(account=account).first()
    else:
        this_individual = individual.objects.create(
            account=account, storage_used=0, storage_limit=5120)
    this_individual_dict = model_to_dict(this_individual)
    return Response({"status": "Success", "credentials": this_individual_dict})


# Individual file upload to NFT
@api_view(["POST"])
def file_upload(request):
    print(request.data)
    account = request.data["account"]
    name = request.data["name"]
    description = request.data["description"]
    metadataURL = request.data['metadata']
    imageURL = request.data['image']
    filesize = float(request.data['filesize'])
    if nft.objects.filter(metadata_url=metadataURL).exists():
        return Response({"status": "Already exists"})
    storage_used = 0
    storage_limit = 5120
    if individual.objects.filter(account=account).exists():
        this_individual = individual.objects.filter(account=account).first()
        storage_used = this_individual.storage_used
        storage_limit = this_individual.storage_limit
    else:
        this_individual = individual.objects.create(
            account=account, storage_used=storage_used, storage_limit=storage_limit)
    if (storage_used + filesize) > storage_limit:
        return Response({"status": "Storage exceeded"})
    else:
        this_individual.storage_used = this_individual.storage_used + filesize
        this_individual.save()
    (token_id, tx_hash) = create_certificate(account, metadataURL)
    response_object = {
        "status": "Success",
        "tokenId": token_id,
        "tx_hash": tx_hash,
    }
    print(response_object)
    nft.objects.create(owner=account,
                       name=name,
                       description=description,
                       token_id=token_id,
                       file_url=imageURL, metadata_url=metadataURL, is_live=True, is_verified=False, issuer=account)
    return Response(response_object)


# Individual file upload to NFT
@api_view(["POST"])
def get_certificates(request):
    print(request.data)
    account = request.data['account']
    account_certificates = list(nft.objects.filter(owner=account))
    response_object = {"status": "Success", "categories": {}}
    for cert in account_certificates:
        mycert = model_to_dict(cert)
        category = mycert["issuer"]
        if category in response_object['categories'].keys():
            response_object['categories'][category].append(mycert)
        else:
            response_object["categories"][category] = [mycert]

    print(response_object)
    return Response(response_object)


@api_view(["GET"])
def issue_eo_certs(request):
    issuecertificates()
    return Response({"status": "Success"})


# @api_view(["POST"])
# def get_certificates(request):
#     print(request.data)
#     token_array = get_ids(request.data["account"])

#     response_object = {"token_array": token_array}
#     return Response(response_object)


# def get_ids(account):
#     balance = myContract.functions.balanceOf(account).call()
#     print(balance)
#     total_supply = myContract.functions.tokenCounter().call()
#     print(total_supply)
#     token_array = []
#     token_id = 1
#     my_token_number = 0
#     while token_id <= total_supply and my_token_number < balance:
#         this_id_owner = myContract.functions.ownerOf(token_id).call()
#         print(this_id_owner)
#         if this_id_owner == account:
#             token_uri = myContract.functions.tokenURI(token_id).call()
#             token_array.append(token_uri)
#             my_token_number = my_token_number + 1
#         token_id = token_id + 1
#     return token_array


# @api_view(["POST"])
# def generate_certificate(request):
#     name = request.data['name']
#     description = request.data['description']
#     account = request.data['account']

#     file = create_image(name)
#     image_filepath = os.path.join(settings.BASE_DIR, "api/certificate.png")
#     print(request.data)

#     metadata = create_metadata(name, description, image_filepath)
#     tx_hash = create_certificate(account, metadata)
#     response_object = {"tx_hash": tx_hash}
#     return Response(response_object)


# def create_metadata(name, description, file):
#     print('here--------------')
#     image_hash = ipfs_client.add(file)
#     print(image_hash)
#     metadata_template["name"] = name
#     metadata_template["description"] = description
#     metadata_template["image"] = "http://ipfs.io/ipfs/" + image_hash[0]["Hash"]
#     metadata_file_path = "./media/metadata_files/metadata.json"
#     with open(metadata_file_path, "w") as file:
#         json.dump(metadata_template, file)
#     metadata_hash = ipfs_client.add(metadata_file_path)
#     metadataURL = "http://ipfs.io/ipfs/" + metadata_hash[0]["Hash"]
#     print(metadataURL)
#     return metadataURL


# @api_view(["GET"])
# def create_credentials(request):
#     password = generatePassword()
#     print(password)
#     return Response({"status": "Success"})
