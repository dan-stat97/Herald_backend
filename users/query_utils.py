from django.db.models import BooleanField, Count, Exists, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce

from core.models import Follow, Profiles
from posts.models import Post
from users.legacy_profiles import ensure_legacy_profile
from users.models import User as UserProfile


def optimize_user_profile_queryset(queryset, auth_user=None):
    queryset = queryset.select_related('user_id')

    legacy_profile_id_sq = Profiles.objects.filter(user_id=OuterRef('user_id_id')).values('id')[:1]
    queryset = queryset.annotate(legacy_profile_id=Subquery(legacy_profile_id_sq))

    posts_count_sq = (
        Post.objects
        .filter(author_id=OuterRef('pk'))
        .values('author_id')
        .annotate(total=Count('id'))
        .values('total')[:1]
    )
    followers_count_sq = (
        Follow.objects
        .filter(following_id=OuterRef('legacy_profile_id'))
        .values('following_id')
        .annotate(total=Count('id'))
        .values('total')[:1]
    )
    following_count_sq = (
        Follow.objects
        .filter(follower_id=OuterRef('legacy_profile_id'))
        .values('follower_id')
        .annotate(total=Count('id'))
        .values('total')[:1]
    )

    queryset = queryset.annotate(
        posts_count_annotated=Coalesce(Subquery(posts_count_sq, output_field=IntegerField()), Value(0)),
        followers_count_annotated=Coalesce(Subquery(followers_count_sq, output_field=IntegerField()), Value(0)),
        following_count_annotated=Coalesce(Subquery(following_count_sq, output_field=IntegerField()), Value(0)),
    )

    is_following_default = Value(False, output_field=BooleanField())
    if not auth_user or not auth_user.is_authenticated:
        return queryset.annotate(is_following_annotated=is_following_default)

    try:
        me = UserProfile.objects.get(user_id=auth_user)
        me_legacy = ensure_legacy_profile(me)
    except UserProfile.DoesNotExist:
        me_legacy = None

    if not me_legacy:
        return queryset.annotate(is_following_annotated=is_following_default)

    is_following_sq = Follow.objects.filter(
        follower_id=me_legacy.id,
        following_id=OuterRef('legacy_profile_id'),
    )
    return queryset.annotate(is_following_annotated=Exists(is_following_sq))
