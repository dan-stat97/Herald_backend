from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import User as UserProfile
from django.shortcuts import get_object_or_404
from core.models import Follow

class FollowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        follower = UserProfile.objects.get(user_id=request.user)
        following = get_object_or_404(UserProfile, pk=pk)
        if Follow.objects.filter(follower_id=follower.id, following_id=following.id).exists():
            return Response({'error': 'Already following'}, status=status.HTTP_409_CONFLICT)
        Follow.objects.create(follower_id=follower.id, following_id=following.id)
        return Response({'success': True})

    @action(detail=True, methods=['delete'])
    def unfollow(self, request, pk=None):
        follower = UserProfile.objects.get(user_id=request.user)
        following = get_object_or_404(UserProfile, pk=pk)
        rel = Follow.objects.filter(follower_id=follower.id, following_id=following.id)
        if rel.exists():
            rel.delete()
        return Response({'success': True})

    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        user = get_object_or_404(UserProfile, pk=pk)
        followers = Follow.objects.filter(following_id=user.id)
        follower_ids = [f.follower_id for f in followers]
        profiles = UserProfile.objects.filter(id__in=follower_ids)
        data = [{'id': p.id, 'username': p.username, 'display_name': p.display_name} for p in profiles]
        return Response(data)

    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        user = get_object_or_404(UserProfile, pk=pk)
        following = Follow.objects.filter(follower_id=user.id)
        following_ids = [f.following_id for f in following]
        profiles = UserProfile.objects.filter(id__in=following_ids)
        data = [{'id': p.id, 'username': p.username, 'display_name': p.display_name} for p in profiles]
        return Response(data)

    @action(detail=False, methods=['get'])
    def check(self, request):
        target_id = request.query_params.get('user_id') or request.query_params.get('target_user_id')
        if not target_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)

        follower = UserProfile.objects.get(user_id=request.user)
        is_following = Follow.objects.filter(follower_id=follower.id, following_id=target_id).exists()
        return Response({'is_following': is_following})

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        follower = UserProfile.objects.get(user_id=request.user)
        is_following = Follow.objects.filter(follower_id=follower.id, following_id=pk).exists()
        return Response({'is_following': is_following})
