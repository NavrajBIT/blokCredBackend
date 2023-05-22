from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
import os

def post_upload_to(instance, filename):
    return 'posts/{}/{}'.format(instance.id, filename)


def custom_upload_to(instance, filename):
    current_time = datetime.now().strftime('%Y%m%d%H%M%S')
    file_ext = os.path.splitext(filename)[1]
    new_filename = f"{current_time}_{instance.id}{file_ext}"
    return f"custom/{new_filename}"


class Image(models.Model):
    image = models.ImageField(upload_to=custom_upload_to)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image.name


class Post(models.Model):
    title = models.CharField(max_length=255)
    heading_image = models.ImageField(upload_to=post_upload_to)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title