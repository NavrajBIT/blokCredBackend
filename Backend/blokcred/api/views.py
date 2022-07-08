from rest_framework.response import Response
from rest_framework.decorators import api_view
import requests
import ipfsApi
import json


ipfs_client = ipfsApi.Client("127.0.0.1", 5001)
metadata_template = {
    "name": "",
    "description": "",
    "image": "",
    "traits": [],
}


@api_view(["GET", "POST"])
def getData(request):
    print(request.data)
    image_hash = ipfs_client.add(request.data["file"])
    print(image_hash["Hash"])
    metadata_template["name"] = request.data["name"]
    metadata_template["description"] = request.data["description"]
    metadata_template["image"] = "http://ipfs.io/ipfs/" + image_hash["Hash"]
    metadata_file_path = "./media/metadata_files/metadata.json"
    with open(metadata_file_path, "w") as file:
        json.dump(metadata_template, file)
    metadata_hash = ipfs_client.add(metadata_file_path)
    response_object = {
        "image_hash": image_hash["Hash"],
        "metadata_hash": metadata_hash[0]["Hash"],
    }

    return Response(response_object)
