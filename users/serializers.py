from rest_framework import serializers
from django.contrib.auth.models import User
from .models import User as UserProfile
from .legacy_profiles import ensure_legacy_profile, get_legacy_profile_for_user_profile
from posts.models import Comment


class UserSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(max_length=100)
    full_name = serializers.CharField(max_length=200)
    display_name = serializers.CharField(max_length=200, required=False, allow_blank=True)


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user_id', 'username', 'display_name', 'full_name', 'email', 'avatar_url', 'bio',
            'followers_count', 'following_count', 'posts_count', 'is_following',
            'notifications_enabled', 'privacy_level', 'email_updates', 'interests', 'onboarding_completed',
            'tier', 'reputation', 'is_verified', 'is_creator', 'auth_provider',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'reputation', 'auth_provider', 'created_at', 'updated_at']

    def get_email(self, obj):
        try:
            return obj.user_id.email if obj.user_id else obj.email
        except Exception:
            return obj.email

    def get_followers_count(self, obj):
        try:
            from core.models import Follow
            legacy_profile = get_legacy_profile_for_user_profile(obj)
            if not legacy_profile:
                return 0
            return Follow.objects.filter(following_id=legacy_profile.id).count()
        except Exception:
            return 0

    def get_following_count(self, obj):
        try:
            from core.models import Follow
            legacy_profile = get_legacy_profile_for_user_profile(obj)
            if not legacy_profile:
                return 0
            return Follow.objects.filter(follower_id=legacy_profile.id).count()
        except Exception:
            return 0

    def get_posts_count(self, obj):
        try:
            from posts.models import Post
            return Post.objects.filter(author_id=obj).count()
        except Exception:
            return 0

    def get_is_following(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
            return False

        try:
            from core.models import Follow
            from users.views import ensure_user_profile

            follower = ensure_user_profile(request.user)
            follower_legacy = ensure_legacy_profile(follower)
            target_legacy = get_legacy_profile_for_user_profile(obj)
            if not follower_legacy or not target_legacy:
                return False
            return Follow.objects.filter(follower_id=follower_legacy.id, following_id=target_legacy.id).exists()
        except Exception:
            return False


class UserReplySerializer(serializers.ModelSerializer):
    post_id = serializers.UUIDField(source='post.id', read_only=True)
    post_content = serializers.CharField(source='post.content', read_only=True)
    post_media_url = serializers.CharField(source='post.media_url', read_only=True, allow_null=True)
    post_media_type = serializers.CharField(source='post.media_type', read_only=True, allow_null=True)
    post_author_username = serializers.SerializerMethodField()
    post_author_display_name = serializers.SerializerMethodField()
    post_author_avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'content',
            'likes_count',
            'created_at',
            'updated_at',
            'post_id',
            'post_content',
            'post_media_url',
            'post_media_type',
            'post_author_username',
            'post_author_display_name',
            'post_author_avatar_url',
        ]
        read_only_fields = fields

    def get_post_author_username(self, obj):
        try:
            return obj.post.author_id.username if obj.post and obj.post.author_id else 'unknown'
        except Exception:
            return 'unknown'

    def get_post_author_display_name(self, obj):
        try:
            return obj.post.author_id.display_name if obj.post and obj.post.author_id else 'Unknown User'
        except Exception:
            return 'Unknown User'

    def get_post_author_avatar_url(self, obj):
        try:
            return obj.post.author_id.avatar_url if obj.post and obj.post.author_id else None
        except Exception:
            return None
