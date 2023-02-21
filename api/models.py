from django.db import models


def name_file(instance, filename):
    return "/".join([str(instance.account), "id_proof", filename])


def template_base_image(instance, filename):
    return "/".join([str(instance.user.account), "template_base_image", filename])


def csv_file(instance, filename):
    return "/".join([str(instance.user.account), "csv_file", filename])


class Admin(models.Model):
    name = models.CharField(max_length=50, default="BIT")
    designation = models.CharField(max_length=50, default="Developer")
    account = models.CharField(max_length=50, unique=True)
    added_by = models.CharField(max_length=50)


class Approver(models.Model):
    name = models.CharField(max_length=50)
    designation = models.CharField(max_length=50)
    email = models.EmailField()


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
    approvers = models.ManyToManyField(Approver)


class Template_Variable(models.Model):
    name = models.CharField(max_length=50)
    x_pos = models.FloatField(default=0)
    y_pos = models.FloatField(default=0)
    width = models.FloatField(default=0)
    height = models.FloatField(default=0)
    color = models.CharField(max_length=10, default="#000000")


class Template(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="default")
    base_image = models.ImageField(upload_to=template_base_image, blank=True, null=True)
    variables = models.ManyToManyField(Template_Variable)
    sector = models.CharField(max_length=50, default="education")
    category = models.CharField(max_length=50, default="custom")
    subscription = models.CharField(max_length=50, default="user")


class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    token_id = models.IntegerField(default=0)
    recipient = models.CharField(max_length=50)
    image_url = models.URLField(max_length=500)
    metadata_url = models.URLField(max_length=500)
    email = models.EmailField()


class Certificate_Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    file = models.FileField(upload_to=csv_file, blank=False, null=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    certificates = models.ManyToManyField(Certificate)
    otp = models.IntegerField(default=0)
