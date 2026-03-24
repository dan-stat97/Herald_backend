# core/social_views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Follow, Bookmark, Profiles, Posts
from .serializers import ProfileSerializer
from .pagination import StandardPagination
import uuid

class FollowViewSet(viewsets.GenericViewSet):
    """
    Follow/Unfollow functionality
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Follow a user"""
        try:
            # Get current user's profile
            current_profile = Profiles.objects.get(user_id=request.user.id)
            
            # Get target profile
            target_profile = Profiles.objects.get(id=pk)
            
            if current_profile.id == target_profile.id:
                return Response({
                    'error': 'Cannot follow yourself'
                }, status=400)
            
            # Create follow relationship
            follow, created = Follow.objects.get_or_create(
                follower=current_profile,
                following=target_profile
            )
            
            if created:
                # Create notification
                from .models import Notifications
                Notifications.objects.create(
                    user=target_profile,
                    type='follow',
                    content=f"{current_profile.username} started following you"
                )
                
                return Response({
                    'success': True,
                    'following': True
                })
            else:
                return Response({
                    'success': True,
                    'following': True,
                    'message': 'Already following'
                })
                
        except Profiles.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        """Unfollow a user"""
        try:
            current_profile = Profiles.objects.get(user_id=request.user.id)
            target_profile = Profiles.objects.get(id=pk)
            
            deleted, _ = Follow.objects.filter(
                follower=current_profile,
                following=target_profile
            ).delete()
            
            return Response({
                'success': True,
                'following': False
            })
            
        except Profiles.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
    
    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        """Get followers of a user"""
        try:
            profile = Profiles.objects.get(id=pk)
            followers_qs = Profiles.objects.filter(
                following__follower=profile
            ).distinct()
            
            page = self.paginate_queryset(followers_qs)
            serializer = ProfileSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
            
        except Profiles.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
    
    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        """Get users that a user is following"""
        try:
            profile = Profiles.objects.get(id=pk)
            following_qs = Profiles.objects.filter(
                follower__following=profile
            ).distinct()
            
            page = self.paginate_queryset(following_qs)
            serializer = ProfileSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
            
        except Profiles.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """Check if current user follows a target user"""
        target_id = request.query_params.get('user_id')
        if not target_id:
            return Response({'error': 'user_id required'}, status=400)
        
        try:
            current_profile = Profiles.objects.get(user_id=request.user.id)
            target_profile = Profiles.objects.get(id=target_id)
            
            is_following = Follow.objects.filter(
                follower=current_profile,
                following=target_profile
            ).exists()
            
            return Response({
                'is_following': is_following
            })
            
        except Profiles.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


class BookmarkViewSet(viewsets.GenericViewSet):
    """
    Bookmark posts — backed by posts.PostBookmark
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def _get_profile(self, request):
        from users.models import User as UserProfile
        return UserProfile.objects.get(user_id=request.user)

    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        """Bookmark a post"""
        from posts.models import Post, PostBookmark
        try:
            profile = self._get_profile(request)
            post = Post.objects.get(id=pk)
            PostBookmark.objects.get_or_create(post=post, user=profile)
            return Response({'success': True, 'bookmarked': True})
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=404)

    @action(detail=True, methods=['post'])
    def unbookmark(self, request, pk=None):
        """Remove bookmark from post"""
        from posts.models import Post, PostBookmark
        try:
            profile = self._get_profile(request)
            post = Post.objects.get(id=pk)
            PostBookmark.objects.filter(post=post, user=profile).delete()
            return Response({'success': True, 'bookmarked': False})
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=404)

    @action(detail=False, methods=['get'])
    def my_bookmarks(self, request):
        """Get current user's bookmarked posts"""
        from posts.models import Post, PostBookmark
        from posts.serializers import PostSerializer
        try:
            profile = self._get_profile(request)
            bookmarked_posts = (
                Post.objects
                .filter(bookmarks__user=profile)
                .select_related('author_id', 'author_id__user_id')
                .order_by('-bookmarks__created_at')
            )
            page = self.paginate_queryset(bookmarked_posts)
            if page is not None:
                serializer = PostSerializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            serializer = PostSerializer(bookmarked_posts, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception:
            return Response({'error': 'Profile not found'}, status=404)