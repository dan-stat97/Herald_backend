from __future__ import annotations

from django.db.models import Q, QuerySet

from core.models import Follow, Profiles
from users.models import User as UserProfile


def get_viewer_profile(request) -> UserProfile | None:
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return None
    try:
        return UserProfile.objects.get(user_id=user)
    except UserProfile.DoesNotExist:
        return None


def get_following_auth_user_ids(viewer_profile: UserProfile | None) -> set[int]:
    if not viewer_profile:
        return set()

    legacy = Profiles.objects.filter(user_id=viewer_profile.user_id_id).first()
    if not legacy:
        return set()

    return set(
        Profiles.objects.filter(
            id__in=Follow.objects.filter(follower_id=legacy.id).values('following_id')
        ).values_list('user_id', flat=True)
    )


def can_view_user_content(viewer_profile: UserProfile | None, target_profile: UserProfile) -> bool:
    level = getattr(target_profile, 'privacy_level', 'public') or 'public'
    if level == 'public':
        return True
    if viewer_profile and viewer_profile.id == target_profile.id:
        return True
    if level == 'private':
        return False
    if level == 'followers' and viewer_profile:
        return target_profile.user_id_id in get_following_auth_user_ids(viewer_profile)
    return False


def filter_visible_posts(queryset: QuerySet, request) -> QuerySet:
    viewer_profile = get_viewer_profile(request)
    if not viewer_profile:
        return queryset.filter(author_id__privacy_level='public')

    following_auth_ids = get_following_auth_user_ids(viewer_profile)
    return queryset.filter(
        Q(author_id__privacy_level='public')
        | Q(author_id__user_id_id=viewer_profile.user_id_id)
        | Q(author_id__privacy_level='followers', author_id__user_id_id__in=following_auth_ids)
    )
