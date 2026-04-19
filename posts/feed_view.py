"""
GET /v1/posts/feed/

Algorithmic "For You" feed.

Authenticated users receive a blended feed of:
  - in-network posts from followed accounts
  - out-of-network posts discovered by ranking

Anonymous or no-follow users receive a globally ranked feed.
"""

import math

from django.core.cache import cache
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .cache_utils import get_post_timeline_cache_version
from .models import Post
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
        try:
            limit = min(max(int(request.query_params.get('limit', 20)), 1), 50)
            page = max(int(request.query_params.get('page', 1)), 1)
        except (TypeError, ValueError):
            limit, page = 20, 1

        cache_version = get_post_timeline_cache_version()
        user_scope = f"user:{request.user.id}" if getattr(request.user, 'is_authenticated', False) else 'anon'
        page_cache_key = f"feed:v2:{user_scope}:p{page}:l{limit}:v{cache_version}"
        ranked_ids_cache_key = f"feed:v2:ranked-ids:{user_scope}:v{cache_version}"

        cached_payload = cache.get(page_cache_key)
        if cached_payload is not None:
            return Response(cached_payload)

        ranked_ids = cache.get(ranked_ids_cache_key)
        if ranked_ids is None:
            ranked_posts = build_twitter_feed(request)
            ranked_ids = [post.id for post in ranked_posts]
            cache.set(ranked_ids_cache_key, ranked_ids, 30)

        total = len(ranked_ids)
        offset = (page - 1) * limit
        page_ids = ranked_ids[offset:offset + limit]
        has_more = total > offset + limit

        if page_ids:
            page_map = {
                post.id: post
                for post in Post.objects.select_related('author_id', 'author_id__user_id').filter(id__in=page_ids)
            }
            page_posts = [page_map[post_id] for post_id in page_ids if post_id in page_map]
        else:
            page_posts = []

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

        cache.set(page_cache_key, payload, 30)
        return Response(payload)
