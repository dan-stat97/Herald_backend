
from rest_framework import serializers
from .models import Post, Comment, PostLike, PostRepost, PostBookmark
from users.serializers import UserProfileSerializer

class CommentSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'likes_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'post', 'author', 'likes_count', 'created_at', 'updated_at']

class PostSerializer(serializers.ModelSerializer):
    author_id = UserProfileSerializer(read_only=True)
    username = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()
    bookmarks_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_reposted = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author_id', 'username', 'display_name', 'avatar_url', 'is_verified', 'is_creator',
            'content', 'media_url', 'media_type', 'likes_count',
            'comments_count', 'shares_count', 'bookmarks_count', 'httn_earned',
            'is_liked', 'is_reposted', 'is_bookmarked',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author_id', 'username', 'display_name', 'avatar_url', 'is_verified', 'is_creator',
            'likes_count', 'comments_count', 'shares_count', 'bookmarks_count', 'httn_earned',
            'is_liked', 'is_reposted', 'is_bookmarked',
            'created_at', 'updated_at'
        ]

    def _get_user_profile(self):
        """Return the users.User profile for the authenticated request user, or None."""
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None
        try:
            from users.models import User as UserProfile
            return UserProfile.objects.get(user_id=request.user)
        except Exception:
            return None

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

    def get_bookmarks_count(self, obj):
        try:
            return obj.bookmarks.count()
        except Exception:
            return 0

    def get_is_liked(self, obj):
        profile = self._get_user_profile()
        if not profile:
            return False
        return PostLike.objects.filter(post=obj, user=profile).exists()

    def get_is_reposted(self, obj):
        profile = self._get_user_profile()
        if not profile:
            return False
        return PostRepost.objects.filter(post=obj, user=profile).exists()

    def get_is_bookmarked(self, obj):
        profile = self._get_user_profile()
        if not profile:
            return False
        return PostBookmark.objects.filter(post=obj, user=profile).exists()

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
                'bookmarks_count': 0,
                'httn_earned': instance.httn_earned,
                'created_at': instance.created_at.isoformat() if instance.created_at else None,
                'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
                'author_id': None,
                'username': 'unknown',
                'display_name': 'Unknown User',
                'avatar_url': None,
                'is_verified': False,
                'is_creator': False,
                'is_liked': False,
                'is_reposted': False,
                'is_bookmarked': False,
            }
            return data

class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content', 'media_url', 'media_type']
