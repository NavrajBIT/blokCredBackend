from rest_framework import serializers
from .models import Post,Image
from django.contrib.auth import get_user_model


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'groups', 'user_permissions')


class ImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ('id', 'image', 'created_at', 'url')

    def get_url(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.image.url)
        else:
            return None

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True)

    def create(self, validated_data):
        author_id = validated_data.pop('author_id')
        try:
            author = User.objects.get(id=author_id)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this ID does not exist')
        post = Post.objects.create(author=author, **validated_data)

        return post

    class Meta:
        model = Post
        fields = ('id', 'title', 'heading_image', 'author', 'author_id', 'content', 'created_at')

