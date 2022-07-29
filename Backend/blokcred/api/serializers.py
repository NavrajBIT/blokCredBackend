from rest_framework import serializers
from .models import nft


class nft_serializer(serializers.ModelSerializer):
    class Meta:
        model = nft
        fields = "__all__"
