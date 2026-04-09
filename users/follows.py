from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Follow, Profiles
from users.models import User as UserProfile
from users.legacy_profiles import ensure_legacy_profile, get_legacy_profile_for_user_profile
from users.views import ensure_user_profile


def _get_target_profile(identifier):
    raw_identifier = str(identifier).strip()
    try:
        UUID(raw_identifier)
        return get_object_or_404(UserProfile, pk=raw_identifier)
    except (TypeError, ValueError):
        pass

    if raw_identifier.isdigit():
        return get_object_or_404(UserProfile, user_id=int(raw_identifier))

    return get_object_or_404(UserProfile, pk=raw_identifier)


def _follow_payload(profile):
    legacy_profile = get_legacy_profile_for_user_profile(profile)
    if not legacy_profile:
        return {'followers_count': 0, 'following_count': 0}
    return {
        'followers_count': Follow.objects.filter(following_id=legacy_profile.id).count(),
        'following_count': Follow.objects.filter(follower_id=legacy_profile.id).count(),
    }

class FollowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        follower = ensure_user_profile(request.user)
        following = _get_target_profile(pk)
        follower_legacy = ensure_legacy_profile(follower)
        following_legacy = ensure_legacy_profile(following)
        if follower.id == following.id:
            return Response({'error': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
        if Follow.objects.filter(follower_id=follower_legacy.id, following_id=following_legacy.id).exists():
            return Response(
                {'error': 'Already following', 'is_following': True, **_follow_payload(following)},
                status=status.HTTP_409_CONFLICT,
            )
        Follow.objects.create(follower_id=follower_legacy.id, following_id=following_legacy.id)
        return Response({'success': True, 'is_following': True, **_follow_payload(following)})

    @action(detail=True, methods=['delete'])
    def unfollow(self, request, pk=None):
        follower = ensure_user_profile(request.user)
        following = _get_target_profile(pk)
        follower_legacy = ensure_legacy_profile(follower)
        following_legacy = ensure_legacy_profile(following)
        rel = Follow.objects.filter(follower_id=follower_legacy.id, following_id=following_legacy.id)
        if rel.exists():
            rel.delete()
        return Response({'success': True, 'is_following': False, **_follow_payload(following)})

    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        user = _get_target_profile(pk)
        user_legacy = ensure_legacy_profile(user)
        followers = Follow.objects.filter(following_id=user_legacy.id)
        follower_auth_ids = list(
            Profiles.objects.filter(id__in=followers.values_list('follower_id', flat=True)).values_list('user_id', flat=True)
        )
        profiles = UserProfile.objects.filter(user_id_id__in=follower_auth_ids)
        data = [{'id': p.id, 'username': p.username, 'display_name': p.display_name} for p in profiles]
        return Response(data)

    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        user = _get_target_profile(pk)
        user_legacy = ensure_legacy_profile(user)
        following = Follow.objects.filter(follower_id=user_legacy.id)
        following_auth_ids = list(
            Profiles.objects.filter(id__in=following.values_list('following_id', flat=True)).values_list('user_id', flat=True)
        )
        profiles = UserProfile.objects.filter(user_id_id__in=following_auth_ids)
        data = [{'id': p.id, 'username': p.username, 'display_name': p.display_name} for p in profiles]
        return Response(data)

    @action(detail=False, methods=['get'])
    def check(self, request):
        target_id = request.query_params.get('user_id') or request.query_params.get('target_user_id')
        if not target_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)

        follower = ensure_user_profile(request.user)
        following = _get_target_profile(target_id)
        follower_legacy = ensure_legacy_profile(follower)
        following_legacy = ensure_legacy_profile(following)
        is_following = Follow.objects.filter(follower_id=follower_legacy.id, following_id=following_legacy.id).exists()
        return Response({'is_following': is_following})

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        follower = ensure_user_profile(request.user)
        following = _get_target_profile(pk)
        follower_legacy = ensure_legacy_profile(follower)
        following_legacy = ensure_legacy_profile(following)
        is_following = Follow.objects.filter(follower_id=follower_legacy.id, following_id=following_legacy.id).exists()
        return Response({'is_following': is_following, **_follow_payload(following)})
