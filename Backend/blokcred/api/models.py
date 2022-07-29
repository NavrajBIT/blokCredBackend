from django.db import models


class admin(models.Model):
    name = models.CharField(max_length=50, default="BIT")
    designation = models.CharField(max_length=50, default="Developer")
    account = models.CharField(max_length=50)
    added_by = models.CharField(max_length=50)


class nft(models.Model):
    owner = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    token_id = models.IntegerField()
    file_url = models.CharField(max_length=500)
    metadata_url = models.CharField(max_length=500)
    is_live = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    issuer = models.CharField(max_length=50, default=owner)


class issuer(models.Model):
    account = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    added_by = models.CharField(max_length=50)
    contract_address = models.CharField(max_length = 50)
    total_certificates = models.IntegerField(default=0)

class destination(models.Model):
    account = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    added_by = models.CharField(max_length=50)
    contract_address = models.CharField(max_length = 50)
    frame = models.CharField(max_length=500)
    total_certificates = models.IntegerField(default=0)

class kpi(models.Model):
    id = models.IntegerField(primary_key=True)
    total_certificates = models.IntegerField()
    only_certificates = models.IntegerField(default=0)
    only_souvenirs = models.IntegerField(default=0)