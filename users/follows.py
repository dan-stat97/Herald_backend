from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import User as UserProfile
from django.shortcuts import get_object_or_404
from django.db.models import Q
from core.models import Follow
from users.views import ensure_user_profile


def _get_target_profile(identifier):
    return get_object_or_404(UserProfile, Q(pk=identifier) | Q(user_id=identifier))


def _follow_payload(profile):
    return {
        'followers_count': Follow.objects.filter(following_id=profile.id).count(),
        'following_count': Follow.objects.filter(follower_id=profile.id).count(),
    }

class FollowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        follower = ensure_user_profile(request.user)
        following = _get_target_profile(pk)
        if follower.id == following.id:
            return Response({'error': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
        if Follow.objects.filter(follower_id=follower.id, following_id=following.id).exists():
            return Response(
                {'error': 'Already following', 'is_following': True, **_follow_payload(following)},
                status=status.HTTP_409_CONFLICT,
            )
        Follow.objects.create(follower_id=follower.id, following_id=following.id)
        return Response({'success': True, 'is_following': True, **_follow_payload(following)})

    @action(detail=True, methods=['delete'])
    def unfollow(self, request, pk=None):
        follower = ensure_user_profile(request.user)
        following = _get_target_profile(pk)
        rel = Follow.objects.filter(follower_id=follower.id, following_id=following.id)
        if rel.exists():
            rel.delete()
        return Response({'success': True, 'is_following': False, **_follow_payload(following)})

    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        user = _get_target_profile(pk)
        followers = Follow.objects.filter(following_id=user.id)
        follower_ids = [f.follower_id for f in followers]
        profiles = UserProfile.objects.filter(id__in=follower_ids)
        data = [{'id': p.id, 'username': p.username, 'display_name': p.display_name} for p in profiles]
        return Response(data)

    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        user = _get_target_profile(pk)
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

        follower = ensure_user_profile(request.user)
        following = _get_target_profile(target_id)
        is_following = Follow.objects.filter(follower_id=follower.id, following_id=following.id).exists()
        return Response({'is_following': is_following})

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        follower = ensure_user_profile(request.user)
        following = _get_target_profile(pk)
        is_following = Follow.objects.filter(follower_id=follower.id, following_id=following.id).exists()
        return Response({'is_following': is_following, **_follow_payload(following)})
