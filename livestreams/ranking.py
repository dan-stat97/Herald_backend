import math
import re
from functools import lru_cache

from django.db import connection
from django.db.models import Count, IntegerField, Value
from django.utils import timezone

from core.models import Follow, Profiles
from users.legacy_profiles import ensure_legacy_profile
from users.models import User as UserProfile

from .models import LiveStream


@lru_cache(maxsize=1)
def _existing_tables() -> frozenset:
    """Cache the DB table list once per process lifetime — tables never change at runtime."""
    return frozenset(connection.introspection.table_names())


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


def _stream_terms(stream: LiveStream) -> set[str]:
    host = getattr(stream, 'user', None)
    return _safe_terms([
        getattr(stream, 'title', ''),
        getattr(stream, 'description', ''),
        getattr(host, 'username', '') if host else '',
        getattr(host, 'display_name', '') if host else '',
        getattr(host, 'bio', '') if host else '',
    ])


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


def _interest_terms(profile: UserProfile | None) -> set[str]:
    if not profile:
        return set()
    return _safe_terms(getattr(profile, 'interests', []))


def _live_score(stream: LiveStream, *, followed_ids: set[str], interest_terms: set[str]) -> float:
    host = getattr(stream, 'user', None)
    host_auth_id = str(getattr(host, 'user_id_id', '') or '')
    terms = _stream_terms(stream)
    overlap = len(interest_terms & terms)

    started_reference = stream.started_at or stream.created_at
    age_hours = max((timezone.now() - started_reference).total_seconds() / 3600.0, 0.15)
    momentum = (
        (getattr(stream, 'viewer_count', 0) or 0) * 1.4
        + (getattr(stream, 'chat_activity', 0) or 0) * 2.2
        + (getattr(stream, 'donation_activity', 0) or 0) * 3.5
    )
    score = (momentum + 5.0) / math.pow(age_hours + 1.4, 0.62)
    score += max(0.0, 26.0 - min(age_hours, 18.0) * 1.2)

    if host_auth_id and host_auth_id in followed_ids:
        score += 30.0
    if overlap:
        score += overlap * 9.0
    if host and getattr(host, 'is_verified', False):
        score += 4.0
    if host and getattr(host, 'is_creator', False):
        score += 3.0
    if host and getattr(host, 'reputation', 0):
        score += min(float(host.reputation) / 100.0, 5.0)

    return score


def _scheduled_score(stream: LiveStream, *, followed_ids: set[str], interest_terms: set[str]) -> float:
    host = getattr(stream, 'user', None)
    host_auth_id = str(getattr(host, 'user_id_id', '') or '')
    terms = _stream_terms(stream)
    overlap = len(interest_terms & terms)

    start_at = stream.scheduled_for or stream.created_at
    hours_until = max((start_at - timezone.now()).total_seconds() / 3600.0, 0.0)
    soonness = 26.0 if hours_until <= 1 else 18.0 if hours_until <= 6 else 10.0 if hours_until <= 24 else max(0.0, 6.0 - min(hours_until, 96.0) / 24.0)
    score = soonness

    if host_auth_id and host_auth_id in followed_ids:
        score += 28.0
    if overlap:
        score += overlap * 8.0
    if getattr(stream, 'thumbnail_url', None):
        score += 2.0
    if host and getattr(host, 'is_verified', False):
        score += 3.0
    if host and getattr(host, 'is_creator', False):
        score += 2.5

    return score


def rank_streams_for_discovery(queryset, request, candidate_limit: int = 180):
    profile = _get_profile(getattr(request, 'user', None))
    followed_ids = _followed_author_ids(profile)
    interest_terms = _interest_terms(profile)

    tables = _existing_tables()
    annotated_queryset = queryset.select_related('user')

    if 'stream_chat_messages' in tables:
        annotated_queryset = annotated_queryset.annotate(
            chat_activity=Count('chat_messages', distinct=True)
        )
    else:
        annotated_queryset = annotated_queryset.annotate(
            chat_activity=Value(0, output_field=IntegerField())
        )

    if 'stream_donations' in tables:
        annotated_queryset = annotated_queryset.annotate(
            donation_activity=Count('donations', distinct=True)
        )
    else:
        annotated_queryset = annotated_queryset.annotate(
            donation_activity=Value(0, output_field=IntegerField())
        )

    candidates = list(
        annotated_queryset[:candidate_limit]
    )
    if not candidates:
        return []

    status_value = getattr(candidates[0], 'status', None)
    scored = []
    for stream in candidates:
        if status_value == 'live':
            score = _live_score(stream, followed_ids=followed_ids, interest_terms=interest_terms)
        else:
            score = _scheduled_score(stream, followed_ids=followed_ids, interest_terms=interest_terms)
        scored.append((score, stream))

    scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    return [stream for _, stream in scored]
