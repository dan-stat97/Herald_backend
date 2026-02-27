from rest_framework import serializers
from .models import Post
from users.serializers import UserProfileSerializer

class PostSerializer(serializers.ModelSerializer):
    author_id = UserProfileSerializer(read_only=True)
    class Meta:
        model = Post
        fields = [
            'id', 'author_id', 'content', 'media_url', 'media_type', 'likes_count',
            'comments_count', 'shares_count', 'httn_earned', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author_id', 'likes_count', 'comments_count', 'shares_count', 'httn_earned', 'created_at', 'updated_at']

class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content', 'media_url', 'media_type']
