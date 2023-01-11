from django.db import models


def name_file(instance, filename):
    return "/".join([ str(instance.account), "id_proof", filename])


class Admin(models.Model):
    name = models.CharField(max_length=50, default="BIT")
    designation = models.CharField(max_length=50, default="Developer")
    account = models.CharField(max_length=50, unique=True)
    added_by = models.CharField(max_length=50)


class User(models.Model):
    account = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=500, blank=True)
    website = models.CharField(max_length=25, blank=True)
    email = models.CharField(max_length=25, blank=True)
    contact = models.IntegerField(blank=True, null=True)
    regId = models.CharField(max_length=50, blank=True)
    idProof = models.ImageField(upload_to=name_file, blank=True, null=True)
    comment = models.CharField(max_length=100, blank=True)
    status_option = (
        ("unverified", "unverified"),
        ("in_progress", "in_progress"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Revoked", "Revoked"),
    )
    status = models.CharField(
        max_length=20, choices=status_option, default="unverified"
    )
    contract_address = models.CharField(max_length=50, blank=True)
    total_certificates = models.IntegerField(default=0)
    total_souvenirs = models.IntegerField(default=0)
    frames = models.JSONField(blank=True, default=dict)
    certificates = models.JSONField(blank=True, default=dict)
    storage_used = models.FloatField(default=0)
    storage_limit = models.FloatField(default=5120)
    nft_quota = models.IntegerField(default=0)
