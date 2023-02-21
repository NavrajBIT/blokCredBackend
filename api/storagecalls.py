import requests
import json
from django.conf import settings
import os
from .contractcalls import get_nft_category
from .models import User
import urllib.request
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

FILE_ROOT = os.path.join(settings.BASE_DIR, "api")
BASE_DIR = settings.BASE_DIR


def upload_image(file):
    url = "https://api.web3.storage/upload"
    files = {"file": file}
    print("uploading image")
    response = requests.post(
        url,
        files=files,
        headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWQ6ZXRocjoweGQyRjVFZkI5QmZFOThhOGQ4YkQ0NzVmMTg4OTU5N2YxQ2M2QzBiMkIiLCJpc3MiOiJ3ZWIzLXN0b3JhZ2UiLCJpYXQiOjE2NTg0OTc1NzYxNzksIm5hbWUiOiJibG9rY3JlZCJ9.VwdALjKL1nRP9uiKkjlAnDcK7x2_RZi-28viJ4sXNgU"
        },
    )
    print(response.json())
    cid = response.json()["cid"]
    file_url = "https://" + cid + ".ipfs.dweb.link"
    return file_url


def upload_metadata(filepath):
    url = "https://api.web3.storage/upload"
    files = {"file": open(filepath, "rb")}
    response = requests.post(
        url,
        files=files,
        headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWQ6ZXRocjoweGQyRjVFZkI5QmZFOThhOGQ4YkQ0NzVmMTg4OTU5N2YxQ2M2QzBiMkIiLCJpc3MiOiJ3ZWIzLXN0b3JhZ2UiLCJpYXQiOjE2NTg0OTc1NzYxNzksIm5hbWUiOiJibG9rY3JlZCJ9.VwdALjKL1nRP9uiKkjlAnDcK7x2_RZi-28viJ4sXNgU"
        },
    )
    cid = response.json()["cid"]
    file_url = "https://" + cid + ".ipfs.dweb.link"
    return file_url


def get_metadata_url(asset_name, asset_description, image):
    image_url = upload_image(image)
    metadata = {
        "name": asset_name,
        "description": asset_description,
        "image": image_url,
    }
    metadata_filepath = os.path.join(FILE_ROOT, "metadata.json")
    with open(metadata_filepath, "w") as metadata_file:
        json.dump(metadata, metadata_file)
    metadata_url = upload_metadata(metadata_filepath)
    return metadata_url, image_url


def get_all_nfts(account):
    url = (
        "https://polygon-mainnet.g.alchemy.com/v2/4H5vwII7kCyZ4CabkkYlwtRiagTT-ZOG/getNFTs?owner="
        + account
    )
    response = requests.get(url=url)
    raw_data = response.json()
    all_nfts = []
    for nft in raw_data["ownedNfts"]:
        nft_data = {
            "contract": nft["contract"]["address"],
            "name": nft["title"],
            "description": nft["description"],
            "image": nft["media"][0]["raw"],
            "is_verified": False,
        }
        all_nfts.append(nft_data)
    all_nfts_sorted = {}
    for nft in all_nfts:
        if nft["contract"] in all_nfts_sorted.keys():
            all_nfts_sorted[nft["contract"]].append(nft)
        else:
            all_nfts_sorted[nft["contract"]] = [nft]
    all_nfts_with_category = {}
    for contract in all_nfts_sorted.keys():
        if User.objects.filter(contract_address=contract).exists():
            user = User.objects.get(contract_address=contract)
            is_verified = user.status == "Approved"
        else:
            is_verified = False
        category = get_nft_category(contract)
        all_nfts_with_category[category] = all_nfts_sorted[contract]
        for i in range(len(all_nfts_with_category[category])):
            all_nfts_with_category[category][i]["is_verified"] = is_verified
    return all_nfts_with_category


def add_frame(base_image, frame_name, user):
    # response = requests.get(url=frame_url, stream=True)
    # print(response.json())
    # response.json
    dir_path = str(BASE_DIR) + "/media/" + user.account + "/frames/"
    frame_filepath = dir_path + frame_name
    # frame_image = Image.open(response.raw)
    frame_image = Image.open(frame_filepath)
    base_image = Image.open(base_image)
    frame_image = frame_image.resize((1920, 1080))
    base_image = base_image.resize((1920, 1080))
    base_image.paste(frame_image, (0, 0), frame_image)
    return base_image
