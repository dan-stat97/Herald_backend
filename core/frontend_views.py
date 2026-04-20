import re
from collections import Counter
from pathlib import Path

from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django.views.generic import TemplateView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.models import Post
from posts.serializers import PostSerializer
from core.pagination import StandardPagination
from users.models import User as UserProfile
from users.query_utils import attach_user_profile_metrics, optimize_user_profile_queryset


SEARCH_TOKEN_SPLIT_RE = re.compile(r"[\s_-]+")
SEARCH_CACHE_TTL_SECONDS = 20


def _normalized_search_variants(query: str) -> tuple[str, set[str], list[str]]:
    raw = (query or "").strip()
    cleaned = raw.lstrip("#").strip()
    normalized = re.sub(r"\s+", " ", cleaned.replace("_", " ").replace("-", " ")).strip().lower()
    if not normalized:
        return "", set(), []

    tokens = [token for token in SEARCH_TOKEN_SPLIT_RE.split(normalized) if token]
    underscore = "_".join(tokens)
    hyphen = "-".join(tokens)
    spaced = " ".join(tokens)

    variants = {
        cleaned,
        normalized,
        spaced,
        underscore,
        hyphen,
        f"#{underscore}",
        f"#{hyphen}",
        f"#{spaced}",
    }
    return normalized, {variant.lower() for variant in variants if variant}, tokens


def _build_post_search_queryset(query: str):
    normalized, variants, tokens = _normalized_search_variants(query)
    if not normalized:
        return Post.objects.none()

    clause = Q()
    for variant in variants:
        clause |= Q(content__icontains=variant)

    # If the literal variant misses, still allow "Super Eagles" to match
    # "super_eagles" by requiring all tokens to be present somewhere.
    if tokens:
        token_clause = Q()
        for token in tokens:
            token_clause &= Q(content__icontains=token)
        clause |= token_clause

    return (
        Post.objects.filter(clause)
        .select_related("author_id", "author_id__user_id")
        .order_by("-likes_count", "-comments_count", "-created_at")
    )


def _build_user_search_queryset(query: str):
    normalized, variants, tokens = _normalized_search_variants(query)
    if not normalized:
        return UserProfile.objects.none()

    clause = Q()
    for variant in variants:
        clause |= (
            Q(username__icontains=variant)
            | Q(display_name__icontains=variant)
            | Q(full_name__icontains=variant)
            | Q(bio__icontains=variant)
        )

    if tokens:
        token_clause = Q()
        for token in tokens:
            token_clause |= (
                Q(username__icontains=token)
                | Q(display_name__icontains=token)
                | Q(full_name__icontains=token)
                | Q(bio__icontains=token)
            )
        clause |= token_clause

    return optimize_user_profile_queryset(
        UserProfile.objects.filter(clause).order_by("-reputation", "-created_at")
    )


def _search_text_score(value: str | None, normalized: str, tokens: list[str]) -> int:
    text = (value or "").strip().lower()
    if not text:
        return 0
    score = 0
    if text == normalized:
        score += 120
    elif text.startswith(normalized):
        score += 90
    elif normalized in text:
        score += 60

    for token in tokens:
        if token == normalized:
            continue
        if token in text:
            score += 12
    return score


def _sort_user_search_results(users, query: str):
    normalized, _, tokens = _normalized_search_variants(query)
    if not normalized:
        return list(users)

    def score(profile: UserProfile):
        return (
            _search_text_score(profile.username, normalized, tokens) * 4
            + _search_text_score(profile.display_name, normalized, tokens) * 3
            + _search_text_score(profile.full_name, normalized, tokens) * 2
            + _search_text_score(profile.bio, normalized, tokens)
            + int(getattr(profile, "reputation", 0) or 0)
        )

    return sorted(
        users,
        key=lambda profile: (
            score(profile),
            int(getattr(profile, "reputation", 0) or 0),
            getattr(profile, "created_at", None) or 0,
        ),
        reverse=True,
    )


def _serialize_search_users(users, request):
    profiles = attach_user_profile_metrics(users, getattr(request, "user", None))
    payload = []
    for profile in profiles:
        payload.append(
            {
                "id": str(profile.id),
                "user_id": profile.user_id_id,
                "username": profile.username,
                "display_name": profile.display_name,
                "full_name": profile.full_name,
                "avatar_url": profile.avatar_url,
                "bio": profile.bio,
                "followers_count": int(getattr(profile, "followers_count_annotated", 0) or 0),
                "following_count": int(getattr(profile, "following_count_annotated", 0) or 0),
                "posts_count": int(getattr(profile, "posts_count_annotated", 0) or 0),
                "is_following": bool(getattr(profile, "is_following_annotated", False)),
                "tier": profile.tier,
                "reputation": profile.reputation,
                "is_verified": profile.is_verified,
                "is_creator": profile.is_creator,
                "created_at": profile.created_at,
            }
        )
    return payload


class ApiHealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class ApiHealthDbView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return Response({"status": "ok", "database": "connected"})
        except Exception as exc:
            return Response({"status": "error", "database": str(exc)}, status=500)


class ApiHealthAuthView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok", "authenticated": True, "user_id": request.user.id})


class TrendingTopicsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = min(int(request.query_params.get("limit", 10)), 100)
        posts = Post.objects.order_by("-created_at").values_list("content", flat=True)[:1000]

        hashtag_pattern = re.compile(r"#([A-Za-z0-9_]+)")
        counter = Counter()

        for content in posts:
            if not content:
                continue
            tags = hashtag_pattern.findall(content)
            counter.update(tag.lower() for tag in tags)

        data = [
            {
                "name": f"#{topic}",
                "topic": topic,
                "tag": f"#{topic}",
                "posts_count": count,
            }
            for topic, count in counter.most_common(limit)
        ]
        return Response(data)


class SearchPostsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q") or request.query_params.get("query")
        if not query:
            return Response({"data": [], "pagination": {"page": 1, "limit": 20, "total": 0, "total_pages": 0}})

        queryset = _build_post_search_queryset(query)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PostSerializer(
            page,
            many=True,
            context={"request": request, "_post_list": list(page), "_author_summary_only": True},
        )
        return paginator.get_paginated_response(serializer.data)


class UnifiedSearchView(APIView):
    """GET /search/?q=... — returns both users and posts in one call."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = (request.query_params.get('q') or
                 request.query_params.get('query') or '').strip()
        if not query:
            return Response({'users': [], 'posts': []})

        limit = min(int(request.query_params.get('limit', 10)), 50)
        normalized, _, _ = _normalized_search_variants(query)
        viewer_scope = f"user:{request.user.id}" if request.user.is_authenticated else "anon"
        cache_key = f"unified-search:{viewer_scope}:{normalized}:{limit}"
        cached_payload = cache.get(cache_key)
        if cached_payload is not None:
            return Response(cached_payload)

        users_candidates = list(_build_user_search_queryset(query)[:limit * 4])
        users_ranked = _sort_user_search_results(users_candidates, query)[:limit]
        users_data = _serialize_search_users(users_ranked, request)

        posts_qs = _build_post_search_queryset(query)[: limit * 2]
        posts_list = list(posts_qs)
        posts_data = PostSerializer(
            posts_list,
            many=True,
            context={"request": request, "_post_list": posts_list, "_author_summary_only": True},
        ).data

        payload = {'users': users_data, 'posts': posts_data}
        cache.set(cache_key, payload, SEARCH_CACHE_TTL_SECONDS)
        return Response(payload)


class ApiDocsView(TemplateView):
    template_name = "api/docs.html"

    def _load_sections(self):
        docs_path = Path(__file__).resolve().parent.parent / "BACKEND_API_REFERENCE.md"
        content = docs_path.read_text(encoding="utf-8")

        title = "Herald Backend API"
        sections = []
        current = None

        for raw_line in content.splitlines():
            line = raw_line.rstrip()
            if line.startswith("# "):
                title = line[2:].strip()
                continue
            if line.startswith("## "):
                if current:
                    current["body"] = "\n".join(current["lines"]).strip()
                    sections.append(current)
                current = {
                    "slug": re.sub(r"[^a-z0-9]+", "-", line[3:].strip().lower()).strip("-"),
                    "heading": line[3:].strip(),
                    "lines": [],
                }
                continue
            if current is not None:
                current["lines"].append(line)

        if current:
            current["body"] = "\n".join(current["lines"]).strip()
            sections.append(current)

        endpoint_count = sum(
            1
            for section in sections
            for line in section["body"].splitlines()
            if line.startswith("| `")
        )

        return {
            "title": title,
            "sections": sections,
            "endpoint_count": endpoint_count,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._load_sections())
        return context
