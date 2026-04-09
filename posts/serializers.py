from django.db.models import Count
from rest_framework import serializers
from .models import Post, Comment, PostLike, PostRepost, PostBookmark
from core.models import Follow, Profiles
from users.legacy_profiles import ensure_legacy_profile

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    def get_author(self, obj):
        author = getattr(obj, 'author', None)
        if not author:
            return None
        return {
            'id': str(author.id),
            'user_id': author.user_id_id,
            'username': author.username,
            'display_name': author.display_name,
            'full_name': author.full_name,
            'email': author.email,
            'avatar_url': author.avatar_url,
            'bio': author.bio,
            'followers_count': 0,
            'following_count': 0,
            'posts_count': 0,
            'is_following': False,
            'notifications_enabled': author.notifications_enabled,
            'privacy_level': author.privacy_level,
            'email_updates': author.email_updates,
            'interests': author.interests,
            'onboarding_completed': author.onboarding_completed,
            'tier': author.tier,
            'reputation': author.reputation,
            'is_verified': author.is_verified,
            'is_creator': author.is_creator,
            'auth_provider': author.auth_provider,
            'created_at': author.created_at,
            'updated_at': author.updated_at,
        }

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'likes_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'post', 'author', 'likes_count', 'created_at', 'updated_at']

class PostSerializer(serializers.ModelSerializer):
    author_id = serializers.SerializerMethodField()
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

    def _get_posts_for_cache(self):
        posts = self.context.get('_post_list')
        if posts is None:
            instance = getattr(self, 'instance', None)
            if instance is None:
                posts = []
            elif isinstance(instance, (list, tuple)):
                posts = list(instance)
            else:
                posts = [instance]
        return posts

    def _ensure_list_caches(self):
        cached = self.context.get('_post_serializer_caches')
        if cached is not None:
            return cached

        posts = [post for post in self._get_posts_for_cache() if getattr(post, 'author_id', None)]
        author_profiles = []
        seen_author_ids = set()
        for post in posts:
            author = post.author_id
            if author and author.id not in seen_author_ids:
                seen_author_ids.add(author.id)
                author_profiles.append(author)

        author_auth_ids = [author.user_id_id for author in author_profiles if getattr(author, 'user_id_id', None)]
        post_ids = [post.id for post in posts]

        legacy_profiles = Profiles.objects.filter(user_id__in=author_auth_ids)
        legacy_by_auth_user_id = {legacy.user_id: legacy for legacy in legacy_profiles}

        missing_legacy_auth_ids = [auth_id for auth_id in author_auth_ids if auth_id not in legacy_by_auth_user_id]
        author_by_auth_user_id = {author.user_id_id: author for author in author_profiles}
        for auth_id in missing_legacy_auth_ids:
            author = author_by_auth_user_id.get(auth_id)
            if not author:
                continue
            legacy = ensure_legacy_profile(author)
            if legacy:
                legacy_by_auth_user_id[auth_id] = legacy

        legacy_ids = [legacy.id for legacy in legacy_by_auth_user_id.values()]
        followers_count_by_legacy_id = {
            row['following_id']: row['count']
            for row in Follow.objects.filter(following_id__in=legacy_ids)
            .values('following_id')
            .annotate(count=Count('id'))
        }
        following_count_by_legacy_id = {
            row['follower_id']: row['count']
            for row in Follow.objects.filter(follower_id__in=legacy_ids)
            .values('follower_id')
            .annotate(count=Count('id'))
        }
        posts_count_by_auth_user_id = {
            row['author_id']: row['count']
            for row in Post.objects.filter(author_id__in=author_auth_ids)
            .values('author_id')
            .annotate(count=Count('id'))
        }

        liked_post_ids = set()
        reposted_post_ids = set()
        bookmarked_post_ids = set()
        profile = self._get_user_profile()
        if profile and post_ids:
            liked_post_ids = set(PostLike.objects.filter(user=profile, post_id__in=post_ids).values_list('post_id', flat=True))
            reposted_post_ids = set(PostRepost.objects.filter(user=profile, post_id__in=post_ids).values_list('post_id', flat=True))
            bookmarked_post_ids = set(PostBookmark.objects.filter(user=profile, post_id__in=post_ids).values_list('post_id', flat=True))

        is_following_by_author_id = {}
        if profile and author_auth_ids:
            follower_legacy = ensure_legacy_profile(profile)
            if follower_legacy:
                followed_legacy_ids = set(
                    Follow.objects.filter(
                        follower_id=follower_legacy.id,
                        following_id__in=legacy_ids,
                    ).values_list('following_id', flat=True)
                )
                for author in author_profiles:
                    legacy = legacy_by_auth_user_id.get(author.user_id_id)
                    is_following_by_author_id[author.id] = bool(legacy and legacy.id in followed_legacy_ids)

        author_payload_by_author_id = {}
        for author in author_profiles:
            legacy = legacy_by_auth_user_id.get(author.user_id_id)
            legacy_id = legacy.id if legacy else None
            author_payload_by_author_id[author.id] = {
                'id': str(author.id),
                'user_id': author.user_id_id,
                'username': author.username,
                'display_name': author.display_name,
                'full_name': author.full_name,
                'email': author.email,
                'avatar_url': author.avatar_url,
                'bio': author.bio,
                'followers_count': followers_count_by_legacy_id.get(legacy_id, 0) if legacy_id else 0,
                'following_count': following_count_by_legacy_id.get(legacy_id, 0) if legacy_id else 0,
                'posts_count': posts_count_by_auth_user_id.get(author.user_id_id, 0),
                'is_following': is_following_by_author_id.get(author.id, False),
                'notifications_enabled': author.notifications_enabled,
                'privacy_level': author.privacy_level,
                'email_updates': author.email_updates,
                'interests': author.interests,
                'onboarding_completed': author.onboarding_completed,
                'tier': author.tier,
                'reputation': author.reputation,
                'is_verified': author.is_verified,
                'is_creator': author.is_creator,
                'auth_provider': author.auth_provider,
                'created_at': author.created_at,
                'updated_at': author.updated_at,
            }

        cached = {
            'author_payload_by_author_id': author_payload_by_author_id,
            'liked_post_ids': liked_post_ids,
            'reposted_post_ids': reposted_post_ids,
            'bookmarked_post_ids': bookmarked_post_ids,
        }
        self.context['_post_serializer_caches'] = cached
        return cached

    def _get_user_profile(self):
        """Return the users.User profile for the authenticated request user, or None.
        Result is cached in serializer context so list serialisation only hits the DB once."""
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None
        _SENTINEL = object()
        cached = self.context.get('_cached_user_profile', _SENTINEL)
        if cached is not _SENTINEL:
            return cached
        try:
            from users.models import User as UserProfile
            profile = UserProfile.objects.get(user_id=request.user)
        except Exception:
            profile = None
        self.context['_cached_user_profile'] = profile
        return profile

    def get_author_id(self, obj):
        try:
            caches = self._ensure_list_caches()
            payload = caches['author_payload_by_author_id'].get(obj.author_id.id)
            if payload is not None:
                return payload
        except Exception:
            pass

        author = obj.author_id
        if not author:
            return None
        return {
            'id': str(author.id),
            'user_id': author.user_id_id,
            'username': author.username,
            'display_name': author.display_name,
            'full_name': author.full_name,
            'email': author.email,
            'avatar_url': author.avatar_url,
            'bio': author.bio,
            'followers_count': 0,
            'following_count': 0,
            'posts_count': 0,
            'is_following': False,
            'notifications_enabled': author.notifications_enabled,
            'privacy_level': author.privacy_level,
            'email_updates': author.email_updates,
            'interests': author.interests,
            'onboarding_completed': author.onboarding_completed,
            'tier': author.tier,
            'reputation': author.reputation,
            'is_verified': author.is_verified,
            'is_creator': author.is_creator,
            'auth_provider': author.auth_provider,
            'created_at': author.created_at,
            'updated_at': author.updated_at,
        }

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
            return obj.bookmarks_count
        except Exception:
            return 0

    def get_is_liked(self, obj):
        try:
            return obj.id in self._ensure_list_caches()['liked_post_ids']
        except Exception:
            profile = self._get_user_profile()
            if not profile:
                return False
            return PostLike.objects.filter(post=obj, user=profile).exists()

    def get_is_reposted(self, obj):
        try:
            return obj.id in self._ensure_list_caches()['reposted_post_ids']
        except Exception:
            profile = self._get_user_profile()
            if not profile:
                return False
            return PostRepost.objects.filter(post=obj, user=profile).exists()

    def get_is_bookmarked(self, obj):
        try:
            return obj.id in self._ensure_list_caches()['bookmarked_post_ids']
        except Exception:
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
