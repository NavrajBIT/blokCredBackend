from rest_framework import serializers
from .models import Admin, User, KPI


class Admin_serializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = "__all__"


class User_serializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
