from scripts.tools import get_account
from brownie import certificate
import json

def deploy_contract():
    account = get_account()
    Certificate = certificate.deploy(
        "Federation of Esports Associations India", "BIT", {"from": account}
    )
    deployed_contract = {"deployed_contract": Certificate.address}
    with open("deployed_contract.json", "w") as file:
        json.dump(deployed_contract, file)

def main():
    deploy_contract()
