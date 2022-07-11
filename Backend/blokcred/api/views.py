from urllib import response
from rest_framework.response import Response
from rest_framework.decorators import api_view
import requests
import ipfsApi
import json, os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from . import contract_config
from django.conf import settings

from .image_creator import create_image

ipfs_client = ipfsApi.Client("127.0.0.1", 5001)
metadata_template = {
    "name": "",
    "description": "",
    "image": "",
    "traits": [],
}

w3 = Web3(Web3.HTTPProvider("https://matic-mumbai.chainstacklabs.com"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

contract_address = contract_config.config["contract_address"]
public_key = contract_config.config["public_key"]
private_key = contract_config.config["private_key"]

contract_filepath = os.path.join(settings.BASE_DIR, "api/compiledContract.json")
with open(contract_filepath, "r") as file:
    contract_json = json.load(file)

abi = contract_json["abi"]
bytecode = contract_json["bytecode"]

myContract = w3.eth.contract(address=contract_address, abi=abi)


@api_view(["POST"])
def get_data(request):
    print(request.data)
    account = request.data["account"]
    file = request.data["file"]
    name = request.data["name"]
    description = request.data["description"]
    image_hash = ipfs_client.add(file)
    metadata_template["name"] = name
    metadata_template["description"] = description
    metadata_template["image"] = "http://ipfs.io/ipfs/" + image_hash["Hash"]
    metadata_file_path = "./media/metadata_files/metadata.json"
    with open(metadata_file_path, "w") as file:
        json.dump(metadata_template, file)
    metadata_hash = ipfs_client.add(metadata_file_path)

    metadataURL = "http://ipfs.io/ipfs/" + metadata_hash[0]["Hash"]
    
    print("here-----------------------------------")
    tx_hash = create_certificate(account, metadataURL)
    response_object = {
        "image_hash": image_hash["Hash"],
        "metadata_hash": metadata_hash[0]["Hash"],
        "tx_hash": tx_hash,
    }
    return Response(response_object)



def create_certificate(account, metadata):
    print("minting NFT...")
    print(w3.isConnected())
    nonce = w3.eth.get_transaction_count(public_key)
    print(f"nonce = {nonce}")
    createCertificate_tx = myContract.functions.createCertificate(
        metadata, account
    ).build_transaction({"from": public_key, "nonce": nonce})
    print("Built transaction...")
    signed_transaction = w3.eth.account.sign_transaction(
        createCertificate_tx, private_key=private_key
    )
    print("Signed transaction transaction...")
    tx_data = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    # receipt = w3.eth.wait_for_transaction_receipt(tx_data)
    return tx_data.hex()


@api_view(["POST"])
def get_certificates(request):
    print(request.data)
    token_array = get_ids(request.data["account"])

    response_object = {"token_array": token_array}
    return Response(response_object)


def get_ids(account):
    balance = myContract.functions.balanceOf(account).call()
    print(balance)
    total_supply = myContract.functions.tokenCounter().call()
    print(total_supply)
    token_array = []
    token_id = 1
    my_token_number = 0
    while token_id <= total_supply and my_token_number < balance:
        this_id_owner = myContract.functions.ownerOf(token_id).call()
        print(this_id_owner)
        if this_id_owner == account:
            token_uri = myContract.functions.tokenURI(token_id).call()
            token_array.append(token_uri)
            my_token_number = my_token_number + 1
        token_id = token_id + 1
    return token_array


@api_view(["POST"])
def generate_certificate(request):
    name = request.data['name']
    description = request.data['description']
    account = request.data['account']

    file = create_image(name)
    image_filepath = os.path.join(settings.BASE_DIR, "api/certificate.png")
    print(request.data)
    
    metadata = create_metadata(name, description, image_filepath)
    tx_hash = create_certificate(account, metadata)
    response_object = {"tx_hash": tx_hash}
    return Response(response_object)


def create_metadata(name, description, file):
    print('here--------------')
    image_hash = ipfs_client.add(file)
    print(image_hash)
    metadata_template["name"] = name
    metadata_template["description"] = description
    metadata_template["image"] = "http://ipfs.io/ipfs/" + image_hash[0]["Hash"]
    metadata_file_path = "./media/metadata_files/metadata.json"
    with open(metadata_file_path, "w") as file:
        json.dump(metadata_template, file)
    metadata_hash = ipfs_client.add(metadata_file_path)
    metadataURL = "http://ipfs.io/ipfs/" + metadata_hash[0]["Hash"]
    print(metadataURL)
    return metadataURL