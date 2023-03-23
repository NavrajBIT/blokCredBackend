from django.conf import settings
from . import contract_config
import json
import os

from web3 import Web3
from web3.middleware import geth_poa_middleware
import time


# Contract data
contract_address = contract_config.config["contract_address"]
public_key = contract_config.config["public_key"]
private_key = contract_config.config["private_key"]
contract_filepath = os.path.join(settings.BASE_DIR, "api/compiledContract.json")
with open(contract_filepath, "r") as file:
    contract_json = json.load(file)
abi = contract_json["abi"]
bytecode = contract_json["bytecode"]


# w3 = Web3(Web3.HTTPProvider("https://polygon-mumbai.g.alchemy.com/v2/CNCI8Fo64T3PScr0dquiyuZr0w1vzvGU"))
# w3 = Web3(Web3.HTTPProvider(""))
# w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:8545"))
w3.eth.defaultAccount = public_key
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
# myContract = w3.eth.contract(address=contract_address, abi=abi)


def deploy_contract(name):
    print("deploying contract.....")
    new_contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(public_key)
    new_tx = new_contract.constructor(name, name).build_transaction(
        {
            "from": public_key,
            "nonce": nonce,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed_tx = w3.eth.account.sign_transaction(new_tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    address = tx_receipt.contractAddress
    return address


def create_certificate(account, metadata, contract_address):
    account = Web3.toChecksumAddress(account)
    my_contract = w3.eth.contract(address=contract_address, abi=abi)
    nonce = w3.eth.get_transaction_count(public_key)
    createCertificate_tx = my_contract.functions.createCertificate(
        metadata, account
    ).build_transaction(
        {
            "from": public_key,
            "nonce": nonce,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed_transaction = w3.eth.account.sign_transaction(
        createCertificate_tx, private_key=private_key
    )
    tx_data = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_data)
    token_id = my_contract.functions.tokenCounter().call()
    print(token_id)
    return token_id



def get_token_id(contract_address):
    my_contract = w3.eth.contract(address=contract_address, abi=abi)
    token_id = int(my_contract.functions.tokenCounter().call()) + 1
    return token_id


def get_nft_category(contract_address):
    contract_address = Web3.toChecksumAddress(contract_address)
    nft_contract = w3.eth.contract(address=contract_address, abi=abi)
    # try:
    contract_name = nft_contract.functions.name().call()
    # except:
    #     contract_name = contract_address
    print(contract_name)
    return contract_name


def get_contract_details(contract_address, token_id):
    token_id = int(token_id)
    my_contract = w3.eth.contract(address=contract_address, abi=abi)
    owner = my_contract.functions.ownerOf(token_id).call()
    metadata_uri = my_contract.functions.tokenURI(token_id).call()
    # event_filter = my_contract.events.Transfer.build_filter()
    # event_filter.args.clientGroups.match_any(0, 0, token_id)
    # print(event_filter)

    return owner, metadata_uri


def check_payment(tx_hash):
    contract_address = '0x75e8Dd78D660C611157a79bF518F04f37Cc7493C'
    contract_filepath = os.path.join(settings.BASE_DIR, "api/tokenContract.json")
    with open(contract_filepath, "r") as file:
        contract_json = json.load(file)
    abi = contract_json["abi"]
    myContract = w3.eth.contract(address=contract_address, abi=abi)
    receipt =  w3.eth.getTransactionReceipt(tx_hash)
    user_address = receipt["from"]
    tx_contract_address = receipt["to"]
    mined = False
    counter = 0
    if contract_address == tx_contract_address:
        while  counter < 5 and (not mined):
            counter = counter + 1
            if receipt["logs"][0]["type"] == "mined":
                mined = True
            else:
                time.sleep(60)    
    result = w3.eth.get_transaction(tx_hash)
    func_obj, func_params = myContract.decode_function_input(result["input"])
    if mined:
        amount = int(w3.fromWei(func_params["amount"], "ether") )       
    else:
        amount = 0
    return amount, user_address