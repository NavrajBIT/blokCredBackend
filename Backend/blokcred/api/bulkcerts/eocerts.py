
from pprint import pprint
from .. import models

import requests
import json
from models import issuer, nft, kpi
from ..contractcalls import create_souvenir

# Importing the PIL library
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


recipients = ['Akhilesh Jatia',
              'Rohit Gupta',
              'Rahul Gupta',
              'Arjun Bansal',
              'Vivek Aggarwal',
              'Abhishek Gupta',
              'Navdeep garg',
              'Ayush Gupta',
              'Ankur Gupta',
              'Sahil Khanna',
              'Akash Sethia',
              'Khagesh Agarwal',
              'Dhananjay Rathi',
              'Prachi Agarwal',
              'Paritosh Ladhani',
              'Aakash Goyal',
              'Nikhil Agarwal',
              'Divij Singhal',
              'Abhi Batra',
              'Sajal Garg',
              'Anubhav Goyal',
              'Shivani Agg Kothari',
              'Sahil Jindal',
              'Abhinav Sarin',
              'Rajat Singhal',
              'Raghav Gupta',
              'Alok Gupta',
              'Roshan Ladhani',
              'Vidur Gupta',
              'Neelambar Agarwal',
              'Harmandeep Kandhal',
              'Ankit Aggarwal',
              'Apurve Goel',
              'Saourabh Khanna',
              'Umesh Agarwal',
              'Devashish Binani',
              'Vidur Chharia',
              'Arjan Dugal',
              'Saurav Agarwal',
              'Ashish Agarwal',
              'Bharat Kothari',
              'Raghav Garg',
              'Rahul Jain',
              'Jyoti Krishna',
              'Karan Ahuja',
              'Mehak Jain',
              'Minal Anand',
              'Avneesh Newar',
              'Saurabh Gupta',
              'Tushar Gupta',
              'Preeti Jatia',
              'Parul Gupta',
              'Aditi Gupta',
              'Anusha Bansal',
              'Neha Aggarwal',
              'Megha Gupta',
              'Shilpi Garg',
              'Sanchi Gupta',
              'Jyoti Gupta',
              'Kritika Khanna',
              'Shweta Sethia',
              'Vanshree Agarwal',
              'Ruchika Rathi',
              'Prashant Agarwal',
              'Alka Ladhani',
              'Tina Goyal',
              'Shilpy Agarwal',
              'Shalini Singhal',
              'Tanisha Batra',
              'Shweta Garg',
              'Pallavi Baisiwal',
              'Himanshu Kothari',
              'Shubhika Jindal',
              'Sunakshi Mohindra',
              'Rikha Singhal',
              'Jessica Gupta',
              'Shilpi Gupta',
              'Poonam Ladhani',
              'Deepika Gupta',
              'Shymaine Pandey Agarwal',
              'Scotchie De Kandhari',
              'Naina Aggarwal',
              'Priyanka Goel',
              'Swatee Khanna',
              'Himani Agarwal',
              'Aditi Binani',
              'Niyati Chharia',
              'Namrita Dugal',
              'Priyanka Agarwal',
              'Shilona Agarwal',
              'Surabhi Kothari',
              'Nikita Garg',
              'Samridhi Jain',
              'Gaurang Krishna',
              'Aanchal Ahuja',
              'Ritesh jain',
              'Vedika Newar',
              'Mudit Mohini',
              'Pallavi Gupta',
              ]


def print_eo_certificate(myname):
    image_filepath = file_root + "template.png"
    img = Image.open(image_filepath)
    I1 = ImageDraw.Draw(img)
    myFont = ImageFont.truetype('arial.ttf', 65)
    I1.text((400, 450), myname, font=myFont, fill=(0, 0, 0))
    filename = str(myname.split(" ")[0]) + str(myname.split(" ")[1]) + ".png"
    # img.show()
    filepath = file_root + filename
    img.save(filepath)
    return filepath


def upload_file(filepath):
    url = 'https://api.web3.storage/upload'
    files = {'file': open(filepath, 'rb')}
    response = requests.post(url, files=files, headers={
                             "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWQ6ZXRocjoweGQyRjVFZkI5QmZFOThhOGQ4YkQ0NzVmMTg4OTU5N2YxQ2M2QzBiMkIiLCJpc3MiOiJ3ZWIzLXN0b3JhZ2UiLCJpYXQiOjE2NTg0OTc1NzYxNzksIm5hbWUiOiJibG9rY3JlZCJ9.VwdALjKL1nRP9uiKkjlAnDcK7x2_RZi-28viJ4sXNgU"})
    print("Recieved response")
    pprint(response.json())
    cid = response.json()['cid']
    filename = filepath.split("/")[-1]
    file_url = "http://ipfs.io/ipfs/" + cid + "/" + filename
    print(file_url)
    return file_url


def create_metadata(image_url):
    metadata = {"name": name, "description": description, "image": image_url}
    image_filename = image_url.split("/")[-1]
    metadata_filename = image_filename.split(".")[0] + ".json"
    metadata_filepath = file_root + metadata_filename
    with open(metadata_filename, "w") as metadata_file:
        json.dump(metadata, metadata_file)
    return metadata_filepath


def issuecertificates():
    myname = "Navraj Sharma"
    myaccount = "0xE858f0370b101cD3F58E03F18BFA1240a591b5Fa"
    image_filepath = print_eo_certificate(myname)
    image_url = upload_file(image_filepath)
    metadata_filepath = create_metadata(image_url)
    metadata_url = upload_file(metadata_filepath)
    issuer_account = "0xAf47726af31C42ef57c771ea078D41cF0B0024A2"
    this_issuer = issuer.objects.filter(account=issuer_account)
    contract_address = this_issuer.contract_address
    (token_id, tx_hash) = create_souvenir(account=myaccount,
                                          contract_address=contract_address, metadata=metadata_url)
    nft.objects.create(owner=myaccount,
                       name=name,
                       description=description,
                       token_id=token_id,
                       file_url=image_url, metadata_url=metadata_url, is_live=True, is_verified=True, issuer=issuer_account)
    kpi_model = kpi.objects.filter(id=1).first()
    total_certificates = kpi_model.total_certificates + 1
    only_certificates = kpi_model.only_certificates + 1
    kpi_model.total_certificates = total_certificates
    kpi_model.only_certificates = only_certificates
    kpi_model.save()
    this_issuer.total_certificates = this_issuer.total_certificates + 1
    this_issuer.save()
    # for recipient in recipients:
    #     print_eo_certificate(recipient)


issuer_account = "0xAf47726af31C42ef57c771ea078D41cF0B0024A2"
description = "Certificate of attendence"
name = "EO event participation"
file_root = "D:\BIT\BlokCred/Backend/Backend/blokcred/api/bulkcerts/eocerts/"
issuecertificates()
