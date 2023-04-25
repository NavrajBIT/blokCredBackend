from django.db import models
import random

def get_random_filename(filename):
    file_extension = filename.split(".")[-1]
    new_filename = str(random.randrange(1000,1000000)) + "." + file_extension
    return new_filename

def name_file(instance, filename):
    return "/".join([str(instance.account), "id_proof", filename])

def sign_file(instance, filename):
    return "/".join([str(instance.account), "sign_note", filename])

def idProofApprover(instance, filename):
    return "/".join([str(instance.name), "idProofApprover", filename])



def template_base_image(instance, filename):
    return "/".join([ str(instance.user.account), "template_base_image", instance.name, ".png"])

def certificate_image(instance, filename):
    return "/".join([ str(instance.user.account), "certificates", str(instance.id) + ".png"])

def certificate_json(instance, filename):
    return "/".join([ str(instance.user.account), "certificates", str(instance.id) + ".json"])

def batch_nft_image(instance, filename):
    filename = filename.replace(" ", "_")
    return "/".join([str(instance.user.account), "dnfts", filename])

def batch_nft_student_image(instance, filename):
    filename = get_random_filename(filename)
    print("Saving image of name ", filename)
    return "/".join(["batch_nft_image", str(instance.wallet_address), filename])





def csv_file(instance, filename):
    filename = get_random_filename(filename)
    return "/".join([str(instance.user.account), "csv_file", filename])

def csv_fileNft(instance, filename):
    filename = get_random_filename(filename)
    return "/".join([str(instance.user.account), "csv_file_nft", filename])


def csv_file(instance, filename):
    filename = get_random_filename(filename)
    return "/".join([str(instance.user.account), "csv_file", filename])


class Admin(models.Model):
    name = models.CharField(max_length=50, default="BIT")
    designation = models.CharField(max_length=50, default="Developer")
    account = models.CharField(max_length=50, unique=True)
    added_by = models.CharField(max_length=50)


class Approver(models.Model):
    name = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50,blank=True)
    designation = models.CharField(max_length=50)
    idProofApprover=models.ImageField(upload_to=idProofApprover, blank=True, null=True)
    email = models.EmailField()


class Subscription(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=200)
    duration_days = models.IntegerField()
    start_Date = models.DateTimeField()
    end_Date = models.DateTimeField()
    
class User(models.Model):
    account = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=500, blank=True)
    website = models.CharField(max_length=25, blank=True)
    email = models.CharField(max_length=25, blank=True)
    country = models.CharField(max_length=25, blank=True)
    issuerName = models.CharField(max_length=50, blank=True)
    issuerLastName = models.CharField(max_length=50, blank=True)
    issuerDesignation = models.CharField(max_length=50, blank=True)
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
    subscription=models.OneToOneField(Subscription,on_delete=models.CASCADE,blank=True, null=True)
    approvers = models.ManyToManyField(Approver)
    noteSignByHigherAuth=models.ImageField(upload_to=sign_file, blank=True, null=True)
    

    

class Template_Variable(models.Model):
    name = models.CharField(max_length=50)
    x_pos = models.FloatField(default=0)
    y_pos = models.FloatField(default=0)
    width = models.FloatField(default=0)
    height = models.FloatField(default=0)
    color = models.CharField(max_length=10, default="#000000")
    type=models.CharField(max_length=50, default="text")
    



class Template(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="default")
    base_image = models.ImageField(upload_to=template_base_image, blank=True, null=True)
    variables = models.ManyToManyField(Template_Variable,related_name='templates')
    sector = models.CharField(max_length=50, default="education")
    category = models.CharField(max_length=50, default="custom")
    subscription = models.CharField(max_length=50, default="user")


class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    token_id = models.IntegerField(default=0)
    recipient = models.CharField(max_length=50)
    email = models.EmailField()
    variable_values = models.JSONField()
    image = models.ImageField(upload_to=certificate_image, blank=True, null=True)
    metadata = models.FileField(upload_to=certificate_json, blank=True, null=True)


class Certificate_Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    file = models.FileField(upload_to=csv_file, blank=False, null=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    certificates = models.ManyToManyField(Certificate)
    fulfilled = models.BooleanField(default=False)
    
class Approval_OTP(models.Model):
    approver = models.ForeignKey(Approver, on_delete=models.CASCADE)
    order = models.ForeignKey(Certificate_Order, on_delete=models.CASCADE)
    otp = models.IntegerField()
    approved = models.BooleanField(default=False)

class Batch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    studentsFile = models.FileField(upload_to=csv_fileNft, blank=True, null=True)
    decription = models.CharField(max_length=500)
    batch_nft_image = models.ImageField(upload_to=batch_nft_image, blank=True, null=True)
    batch_nft_metadata = models.FileField(upload_to=batch_nft_image, blank=True, null=True)
    qr_x_pos = models.FloatField(default = 10)
    qr_y_pos = models.FloatField(default = 10)


class Students(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wallet_address = models.CharField(max_length=50)
    batch_name = models.ForeignKey(Batch, on_delete=models.CASCADE)
    nft_image = models.ImageField(upload_to=batch_nft_image, blank=True, null=True)
    metadata = models.FileField(upload_to=batch_nft_image, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    token_id = models.IntegerField(default=0)
    is_minted = models.BooleanField(default=False)
    email = models.EmailField(null=True, blank=True)