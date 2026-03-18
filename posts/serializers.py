
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
    username = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'author_id', 'username', 'display_name', 'avatar_url', 'is_verified', 'is_creator',
            'content', 'media_url', 'media_type', 'likes_count',
            'comments_count', 'shares_count', 'httn_earned', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author_id', 'username', 'display_name', 'avatar_url', 'is_verified', 'is_creator', 'likes_count', 'comments_count', 'shares_count', 'httn_earned', 'created_at', 'updated_at']
    
    def get_username(self, obj):
        try:
            return obj.author_id.username if obj.author_id else 'unknown'
        except:
            return 'unknown'
    
    def get_display_name(self, obj):
        try:
            return obj.author_id.display_name if obj.author_id else 'Unknown User'
        except:
            return 'Unknown User'
    
    def get_avatar_url(self, obj):
        try:
            return obj.author_id.avatar_url if obj.author_id else None
        except:
            return None

    def get_is_verified(self, obj):
        try:
            return bool(obj.author_id.is_verified) if obj.author_id else False
        except:
            return False

    def get_is_creator(self, obj):
        try:
            return bool(obj.author_id.is_creator) if obj.author_id else False
        except:
            return False
    
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
                'author_id': None,
                'username': 'unknown',
                'display_name': 'Unknown User',
                'avatar_url': None,
                'is_verified': False,
                'is_creator': False
            }
            return data

class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content', 'media_url', 'media_type']
