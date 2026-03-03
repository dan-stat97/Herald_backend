
from rest_framework import serializers
from .models import Post, Comment
from users.serializers import UserProfileSerializer

class CommentSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'likes_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'likes_count', 'created_at', 'updated_at']

class PostSerializer(serializers.ModelSerializer):
    author_id = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'author_id', 'content', 'media_url', 'media_type', 'likes_count',
            'comments_count', 'shares_count', 'httn_earned', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author_id', 'likes_count', 'comments_count', 'shares_count', 'httn_earned', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        try:
            return super().to_representation(instance)
        except Exception as e:
            # Fallback if author serialization fails
            data = {
                'id': str(instance.id),
                'content': instance.content,
                'media_url': instance.media_url,
                'media_type': instance.media_type,
                'likes_count': instance.likes_count,
                'comments_count': instance.comments_count,
                'shares_count': instance.shares_count,
                'httn_earned': instance.httn_earned,
                'created_at': instance.created_at.isoformat() if instance.created_at else None,
                'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
                'author_id': None
            }
            return data

class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content', 'media_url', 'media_type']
