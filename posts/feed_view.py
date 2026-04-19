"""
GET /v1/posts/feed/

Twitter-style algorithmic "For You" feed.

Blend strategy (authenticated users with follows):
  - In-network  (~40%): recent posts from accounts the user follows, scored
                         with VERIFIED_IN_NETWORK_BOOST (×4.0)
  - Out-of-network (~60%): algorithmically ranked posts from everyone else,
                            social-proof gated, VERIFIED_OUT_NETWORK_BOOST (×2.0)

Scoring signals (Twitter HomeGlobalParams calibration):
  W_REPLY=13.5, W_BOOKMARK=2.0, W_RETWEET=1.0, W_LIKE=0.5, W_VIEW=0.005
  + freshness decay: max(exp(-0.003 × age_minutes), 0.6)
  + follow/engagement/interest/live boosts
  + diversity pass: same author ≤ 2× in any 5-post window

Anonymous / no-follows users receive pure global algorithmic ranking.
Responses are cached per-user per-page for 30 seconds.
"""

import math

from django.core.cache import cache
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .cache_utils import get_post_timeline_cache_version
from .ranking import build_twitter_feed
from .serializers import PostSerializer


class PostFeedView(APIView):
    """
    Personalised algorithmic feed — GET /v1/posts/feed/

    Query params:
        page  (int, default 1)
        limit (int, default 20, max 50)
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # ── Parse params ──────────────────────────────────────────────────────
        try:
            limit = min(max(int(request.query_params.get('limit', 20)), 1), 50)
            page  = max(int(request.query_params.get('page',  1)),  1)
        except (TypeError, ValueError):
            limit, page = 20, 1

        # ── Cache lookup ──────────────────────────────────────────────────────
        cache_version = get_post_timeline_cache_version()
        user_scope    = f"user:{request.user.id}" if getattr(request.user, 'is_authenticated', False) else 'anon'
        cache_key     = f"feed:v2:{user_scope}:p{page}:l{limit}:v{cache_version}"

        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        # ── Build ranked list via Twitter-style two-pool algorithm ────────────
        ranked_posts = build_twitter_feed(request)

        # ── Paginate ──────────────────────────────────────────────────────────
        total      = len(ranked_posts)
        offset     = (page - 1) * limit
        page_posts = ranked_posts[offset:offset + limit]
        has_more   = total > offset + limit

        # ── Serialize ─────────────────────────────────────────────────────────
        serializer = PostSerializer(
            page_posts,
            many=True,
            context={
                'request': request,
                '_post_list': page_posts,
                '_author_summary_only': True,
            },
        )

        payload = {
            'data': serializer.data,
            'pagination': {
                'page': page,
                'limit': limit,
                'has_more': has_more,
                'total': total,
                'total_pages': math.ceil(total / limit) if limit else 1,
            },
        }

        cache.set(cache_key, payload, 30)
        return Response(payload)
