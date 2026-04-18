from django.db.models import Count

from core.models import Follow, Profiles
from posts.models import Post
from users.legacy_profiles import ensure_legacy_profile
from users.models import User as UserProfile


def optimize_user_profile_queryset(queryset):
    return queryset.select_related('user_id')


def attach_user_profile_metrics(profiles, auth_user=None):
    profile_list = list(profiles)
    if not profile_list:
        return profile_list

    auth_user_ids = [profile.user_id_id for profile in profile_list if getattr(profile, 'user_id_id', None)]
    legacy_rows = Profiles.objects.filter(user_id__in=auth_user_ids).values('id', 'user_id')
    legacy_id_by_auth_user_id = {row['user_id']: row['id'] for row in legacy_rows}
    legacy_ids = list(legacy_id_by_auth_user_id.values())

    post_counts = {
        row['author_id']: row['total']
        for row in (
            Post.objects
            .filter(author_id__in=profile_list)
            .values('author_id')
            .annotate(total=Count('id'))
        )
    }

    followers_counts = {}
    following_counts = {}
    if legacy_ids:
        followers_counts = {
            row['following_id']: row['total']
            for row in (
                Follow.objects
                .filter(following_id__in=legacy_ids)
                .values('following_id')
                .annotate(total=Count('id'))
            )
        }
        following_counts = {
            row['follower_id']: row['total']
            for row in (
                Follow.objects
                .filter(follower_id__in=legacy_ids)
                .values('follower_id')
                .annotate(total=Count('id'))
            )
        }

    followed_legacy_ids = set()
    if auth_user and getattr(auth_user, 'is_authenticated', False) and legacy_ids:
        try:
            me = UserProfile.objects.get(user_id=auth_user)
            me_legacy = ensure_legacy_profile(me)
            if me_legacy:
                followed_legacy_ids = set(
                    Follow.objects
                    .filter(follower_id=me_legacy.id, following_id__in=legacy_ids)
                    .values_list('following_id', flat=True)
                )
        except UserProfile.DoesNotExist:
            followed_legacy_ids = set()

    for profile in profile_list:
        legacy_id = legacy_id_by_auth_user_id.get(profile.user_id_id)
        profile.posts_count_annotated = int(post_counts.get(profile.user_id_id, 0))
        profile.followers_count_annotated = int(followers_counts.get(legacy_id, 0)) if legacy_id else 0
        profile.following_count_annotated = int(following_counts.get(legacy_id, 0)) if legacy_id else 0
        profile.is_following_annotated = bool(legacy_id and legacy_id in followed_legacy_ids)

    return profile_list
