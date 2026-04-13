import math
import re
from collections import Counter

from django.utils import timezone

from core.models import Follow, Profiles
from livestreams.models import LiveStream
from users.legacy_profiles import ensure_legacy_profile
from users.models import User as UserProfile

from .models import Post, PostBookmark, PostLike, PostRepost


TOKEN_RE = re.compile(r"[A-Za-z0-9_#']+")


def _safe_terms(values) -> set[str]:
    terms: set[str] = set()
    for value in values or []:
        if not value:
            continue
        for token in TOKEN_RE.findall(str(value).lower().replace('-', ' ')):
            cleaned = token.strip().lstrip('#')
            if len(cleaned) >= 3:
                terms.add(cleaned)
    return terms


def _post_terms(post: Post) -> set[str]:
    author = getattr(post, 'author_id', None)
    values = [post.content]
    if author:
        values.extend([
            getattr(author, 'username', ''),
            getattr(author, 'display_name', ''),
            getattr(author, 'bio', ''),
        ])
    return _safe_terms(values)


def _get_profile(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    try:
        return UserProfile.objects.get(user_id=user)
    except UserProfile.DoesNotExist:
        return None


def _followed_author_ids(profile: UserProfile | None) -> set[str]:
    if not profile:
        return set()
    legacy = ensure_legacy_profile(profile)
    if not legacy:
        return set()
    following_auth_user_ids = Profiles.objects.filter(
        id__in=Follow.objects.filter(follower_id=legacy.id).values_list('following_id', flat=True)
    ).values_list('user_id', flat=True)
    return {str(value) for value in following_auth_user_ids}


def _engaged_author_ids(profile: UserProfile | None) -> tuple[set[str], set[str]]:
    if not profile:
        return set(), set()

    recent_likes = PostLike.objects.filter(user=profile).select_related('post__author_id')[:120]
    recent_reposts = PostRepost.objects.filter(user=profile).select_related('post__author_id')[:120]
    recent_bookmarks = PostBookmark.objects.filter(user=profile).select_related('post__author_id')[:120]

    author_ids: set[str] = set()
    term_bag: list[str] = []

    for relation in [*recent_likes, *recent_reposts, *recent_bookmarks]:
        post = getattr(relation, 'post', None)
        author = getattr(post, 'author_id', None)
        if author and getattr(author, 'user_id_id', None):
            author_ids.add(str(author.user_id_id))
        if post:
            term_bag.extend(_post_terms(post))

    return author_ids, set(term_bag)


def _live_author_ids() -> set[str]:
    return {
        str(value)
        for value in LiveStream.objects.filter(status='live').values_list('user__user_id', flat=True)
    }


def _base_post_score(post: Post, *, followed_ids: set[str], engaged_author_ids: set[str], user_terms: set[str], live_author_ids: set[str]) -> float:
    author = getattr(post, 'author_id', None)
    author_auth_id = str(getattr(author, 'user_id_id', '') or '')
    post_terms = _post_terms(post)

    now = timezone.now()
    age_hours = max((now - post.created_at).total_seconds() / 3600.0, 0.2)
    engagement = (
        (post.likes_count or 0) * 1.0
        + (post.comments_count or 0) * 2.2
        + (post.shares_count or 0) * 3.4
        + (post.bookmarks_count or 0) * 2.8
    )
    engagement_velocity = ((engagement + 1.0) / math.pow(age_hours + 2.0, 0.72)) * 3.8
    freshness = max(0.0, 42.0 - (min(age_hours, 96.0) * 0.55))

    score = freshness + engagement_velocity

    if author_auth_id and author_auth_id in followed_ids:
        score += 34.0

    if author_auth_id and author_auth_id in engaged_author_ids:
        score += 18.0

    overlap = len(user_terms & post_terms)
    if overlap:
        score += overlap * 8.5

    hashtag_overlap = len({
        token for token in TOKEN_RE.findall((post.content or '').lower()) if token.startswith('#')
    } & {f'#{term}' for term in user_terms})
    if hashtag_overlap:
        score += hashtag_overlap * 5.0

    if author and getattr(author, 'is_verified', False):
        score += 4.0
    if author and getattr(author, 'is_creator', False):
        score += 3.5
    if author and getattr(author, 'tier', '') == 'premium':
        score += 1.5
    if author and getattr(author, 'reputation', 0):
        score += min(float(author.reputation) / 80.0, 7.0)
    if post.media_url:
        score += 2.5
    if author_auth_id and author_auth_id in live_author_ids:
        score += 12.0

    return score


def rank_feed_posts(queryset, request, candidate_limit: int = 280):
    profile = _get_profile(getattr(request, 'user', None))
    followed_ids = _followed_author_ids(profile)
    engaged_author_ids, engaged_terms = _engaged_author_ids(profile)
    interest_terms = _safe_terms(getattr(profile, 'interests', []) if profile else [])
    user_terms = interest_terms | engaged_terms
    live_author_ids = _live_author_ids()

    candidates = list(queryset[:candidate_limit])
    if not candidates:
        return []

    scored = [
        (
            _base_post_score(
                post,
                followed_ids=followed_ids,
                engaged_author_ids=engaged_author_ids,
                user_terms=user_terms,
                live_author_ids=live_author_ids,
            ),
            post,
        )
        for post in candidates
    ]

    scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)

    selected: list[Post] = []
    author_counts: Counter[str] = Counter()
    remaining = scored[:]

    # Add a light diversity pass so one account does not dominate the page.
    while remaining:
        best_index = 0
        best_adjusted = None
        for index, (score, post) in enumerate(remaining):
            author_key = str(getattr(post.author_id, 'user_id_id', '') or '')
            adjusted = score - (author_counts[author_key] * 6.0)
            if best_adjusted is None or adjusted > best_adjusted:
                best_adjusted = adjusted
                best_index = index

        _, chosen = remaining.pop(best_index)
        author_key = str(getattr(chosen.author_id, 'user_id_id', '') or '')
        author_counts[author_key] += 1
        selected.append(chosen)

    return selected
