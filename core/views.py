# core/views.py
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .pagination import StandardPagination
# core/views.py
from .models import (
    Profiles, Posts, Likes, Reposts, Hashtags,
    Transactions, News, Communities, Causes, Notifications,
    AdCampaigns, PostInteractions, UserRoles, UserSettings, UserTasks, Wallets,
    NewsArticle,
)
from .serializers import (
    ProfileSerializer, PostSerializer, LikeSerializer,
    RepostSerializer, HashtagSerializer, TransactionSerializer,
    NewsSerializer, CommunitySerializer, CauseSerializer,
    NotificationSerializer, CommentSerializer, FollowSerializer, BookmarkSerializer,
)
from rest_framework import serializers
from core.pagination import StandardPagination

import uuid

# Apply csrf_exempt to all views
@method_decorator(csrf_exempt, name='dispatch')
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profiles.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        try:
            profile = Profiles.objects.get(user_id=request.user.id)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except Profiles.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)

    @action(detail=False, methods=['post'])
    def create_from_user(self, request):
        """Create a profile from the authenticated user"""
        if Profiles.objects.filter(user_id=request.user.id).exists():
            return Response({'error': 'Profile already exists'}, status=400)
        
        profile = Profiles.objects.create(
            id=uuid.uuid4(),
            user_id=request.user.id,
            username=request.user.username,
            full_name=request.user.get_full_name() or request.user.username,
            display_name=request.user.username,
            balance=0
        )
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class PostViewSet(viewsets.ModelViewSet):
    queryset = Posts.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        profile = Profiles.objects.get(user_id=self.request.user.id)
        serializer.save(
            user=profile,
            author_id=self.request.user.id
        )

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        profile = Profiles.objects.get(user_id=request.user.id)
        
        like, created = Likes.objects.get_or_create(
            post=post,
            user=profile
        )
        
        if created:
            # Update likes count
            post.likes_count = (post.likes_count or 0) + 1
            post.save()
            
            # Create notification
            if post.user and post.user.user_id != request.user.id:
                Notifications.objects.create(
                    user=post.user,
                    type='like',
                    content=f"{profile.username} liked your post"
                )
            
            return Response({'status': 'liked'})
        return Response({'status': 'already liked'}, status=400)

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        post = self.get_object()
        profile = Profiles.objects.get(user_id=request.user.id)
        
        deleted, _ = Likes.objects.filter(post=post, user=profile).delete()
        
        if deleted:
            post.likes_count = max(0, (post.likes_count or 0) - 1)
            post.save()
            return Response({'status': 'unliked'})
        return Response({'status': 'not liked'}, status=400)

    @action(detail=True, methods=['post'])
    def repost(self, request, pk=None):
        post = self.get_object()
        profile = Profiles.objects.get(user_id=request.user.id)
        
        repost, created = Reposts.objects.get_or_create(
            original_post=post,
            user=profile
        )
        
        if created:
            post.reposts_count = (post.reposts_count or 0) + 1
            post.save()
            return Response({'status': 'reposted'})
        return Response({'status': 'already reposted'}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class LikeViewSet(viewsets.ModelViewSet):
    queryset = Likes.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]


@method_decorator(csrf_exempt, name='dispatch')
class RepostViewSet(viewsets.ModelViewSet):
    queryset = Reposts.objects.all()
    serializer_class = RepostSerializer
    permission_classes = [permissions.IsAuthenticated]


@method_decorator(csrf_exempt, name='dispatch')
class HashtagViewSet(viewsets.ModelViewSet):
    queryset = Hashtags.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = [permissions.IsAuthenticated]


@method_decorator(csrf_exempt, name='dispatch')
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transactions.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]


class NewsArticleSerializer(serializers.ModelSerializer):
    """Serializer for NewsArticle that maps fields to frontend expectations."""
    summary = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    source_type = serializers.SerializerMethodField()
    external_url = serializers.URLField(source='source_url', allow_null=True, read_only=True)
    published_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = NewsArticle
        fields = [
            'id', 'title', 'summary', 'content', 'source', 'source_type',
            'image_url', 'external_url', 'published_at', 'likes_count', 'category',
        ]

    def get_summary(self, obj):
        if obj.content:
            return obj.content[:200] + ('…' if len(obj.content) > 200 else '')
        return None

    def get_source(self, obj):
        return 'Herald Social'

    def get_source_type(self, obj):
        cat = (obj.category or '').lower()
        if 'loveworld' in cat:
            return 'loveworld'
        if 'healing' in cat:
            return 'healing_school'
        if 'external' in cat or 'christian' in cat:
            return 'external'
        return 'herald'


@method_decorator(csrf_exempt, name='dispatch')
class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    """News articles — uses NewsArticle model with extended fields."""
    permission_classes = [permissions.AllowAny]
    serializer_class = NewsArticleSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        try:
            queryset = NewsArticle.objects.all().order_by('-created_at')
            category = self.request.query_params.get('category')
            source_type = self.request.query_params.get('source_type')
            sort = self.request.query_params.get('sort') or '-created_at'

            if category:
                queryset = queryset.filter(category__icontains=category)

            if source_type:
                normalized = source_type.lower()
                if normalized == 'herald':
                    queryset = queryset.exclude(category__icontains='loveworld').exclude(category__icontains='external')
                elif normalized == 'loveworld':
                    queryset = queryset.filter(category__icontains='loveworld')
                elif normalized == 'external':
                    queryset = queryset.filter(category__icontains='external')

            if sort in {'created_at', '-created_at', 'likes_count', '-likes_count'}:
                queryset = queryset.order_by(sort)

            return queryset
        except Exception:
            # Fallback to old News model if new table doesn't exist yet
            return News.objects.none()


@method_decorator(csrf_exempt, name='dispatch')
class CommunityViewSet(viewsets.ModelViewSet):
    queryset = Communities.objects.all()
    serializer_class = CommunitySerializer

    def get_permissions(self):
        # Anyone can list/retrieve communities; write ops require auth
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


@method_decorator(csrf_exempt, name='dispatch')
class CauseViewSet(viewsets.ModelViewSet):
    queryset = Causes.objects.all()
    serializer_class = CauseSerializer
    permission_classes = [permissions.IsAuthenticated]


@method_decorator(csrf_exempt, name='dispatch')
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notifications.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter notifications for the current user"""
        try:
            profile = Profiles.objects.get(user_id=self.request.user.id)
            return Notifications.objects.filter(user=profile).order_by('-created_at')
        except Profiles.DoesNotExist:
            return Notifications.objects.none()

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        try:
            profile = Profiles.objects.get(user_id=request.user.id)
            Notifications.objects.filter(user=profile, is_read=False).update(is_read=True)
            return Response({'status': 'all marked as read'})
        except Profiles.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)


# Optional: Add these if you need CRUD for additional tables
@method_decorator(csrf_exempt, name='dispatch')
class AdCampaignsViewSet(viewsets.ModelViewSet):
    queryset = AdCampaigns.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        # You'll need to create serializers for these if you want to use them
        from rest_framework import serializers
        class AdCampaignsSerializer(serializers.ModelSerializer):
            class Meta:
                model = AdCampaigns
                fields = '__all__'
        return AdCampaignsSerializer


@method_decorator(csrf_exempt, name='dispatch')
class PostInteractionsViewSet(viewsets.ModelViewSet):
    queryset = PostInteractions.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from rest_framework import serializers
        class PostInteractionsSerializer(serializers.ModelSerializer):
            class Meta:
                model = PostInteractions
                fields = '__all__'
        return PostInteractionsSerializer


@method_decorator(csrf_exempt, name='dispatch')
class UserRolesViewSet(viewsets.ModelViewSet):
    queryset = UserRoles.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from rest_framework import serializers
        class UserRolesSerializer(serializers.ModelSerializer):
            class Meta:
                model = UserRoles
                fields = '__all__'
        return UserRolesSerializer


@method_decorator(csrf_exempt, name='dispatch')
class UserSettingsViewSet(viewsets.ModelViewSet):
    queryset = UserSettings.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from rest_framework import serializers
        class UserSettingsSerializer(serializers.ModelSerializer):
            class Meta:
                model = UserSettings
                fields = '__all__'
        return UserSettingsSerializer


@method_decorator(csrf_exempt, name='dispatch')
class UserTasksViewSet(viewsets.ModelViewSet):
    queryset = UserTasks.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from rest_framework import serializers
        class UserTasksSerializer(serializers.ModelSerializer):
            class Meta:
                model = UserTasks
                fields = '__all__'
        return UserTasksSerializer


@method_decorator(csrf_exempt, name='dispatch')
class WalletsViewSet(viewsets.ModelViewSet):
    queryset = Wallets.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from rest_framework import serializers
        class WalletsSerializer(serializers.ModelSerializer):
            class Meta:
                model = Wallets
                fields = '__all__'
        return WalletsSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Posts.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Allow filtering posts"""
        queryset = super().get_queryset()
        
        # Filter by user if provided
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(author_id=user_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create a new post"""
        try:
            # Get the user's profile
            profile = Profiles.objects.get(user_id=self.request.user.id)
            
            # Log for debugging
            print(f"Creating post for user: {self.request.user.id}")
            print(f"Profile ID: {profile.id}")
            print(f"Request data: {self.request.data}")
            
            # Create the post
            serializer.save(
                user=profile,
                author_id=profile.id,  # Use profile.id (UUID)
                is_sponsored=False,
                likes_count=0,
                replies_count=0,
                reposts_count=0
            )
            
        except Profiles.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"error": "Profile not found. Please create a profile first."})
        except Exception as e:
            from rest_framework.exceptions import APIException
            import traceback
            traceback.print_exc()
            raise APIException(f"Error creating post: {str(e)}")
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a post"""
        try:
            post = self.get_object()
            profile = Profiles.objects.get(user_id=request.user.id)
            
            # Check if already liked
            from core.models import Likes
            like, created = Likes.objects.get_or_create(
                post=post,
                user=profile
            )
            
            if created:
                post.likes_count = (post.likes_count or 0) + 1
                post.save()
                return Response({'success': True, 'likes_count': post.likes_count})
            return Response({'success': True, 'message': 'Already liked', 'likes_count': post.likes_count})
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a post"""
        try:
            post = self.get_object()
            profile = Profiles.objects.get(user_id=request.user.id)
            
            from core.models import Likes
            deleted, _ = Likes.objects.filter(post=post, user=profile).delete()
            
            if deleted:
                post.likes_count = max(0, (post.likes_count or 0) - 1)
                post.save()
                return Response({'success': True, 'likes_count': post.likes_count})
            return Response({'success': True, 'message': 'Not liked', 'likes_count': post.likes_count})
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)
