from django.core.cache import cache
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.cache_utils import get_post_timeline_cache_version
from posts.ranking import build_twitter_feed
from posts.serializers import PostSerializer
from users.models import User as UserProfile

from .news_clusters import _build_clusters, build_trending_topics


EXPLORE_TABS = {'for_you', 'trending', 'news', 'sports', 'entertainment'}


def _viewer_interest_terms(request):
    if not getattr(request.user, 'is_authenticated', False):
        return set()
    try:
        profile = UserProfile.objects.only('interests').get(user_id=request.user)
    except UserProfile.DoesNotExist:
        return set()
    terms = set()
    for value in profile.interests or []:
        for token in str(value).lower().replace('-', ' ').split():
            cleaned = token.strip()
            if len(cleaned) >= 3:
                terms.add(cleaned)
    return terms


def _topic_score(topic, interest_terms):
    haystack = ' '.join(
        filter(
            None,
            [
                topic.get('topic', ''),
                topic.get('name', ''),
                topic.get('tag', ''),
            ],
        )
    ).lower()
    overlap = sum(1 for term in interest_terms if term in haystack)
    return (topic.get('posts_count') or 0) * 1.4 + overlap * 160


def _build_explore_for_you(request, limit=18):
    cache_version = get_post_timeline_cache_version()
    user_scope = f"user:{request.user.id}" if getattr(request.user, 'is_authenticated', False) else 'anon'
    cache_key = f"explore:for-you:{user_scope}:l{limit}:v{cache_version}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    interest_terms = _viewer_interest_terms(request)
    topics = build_trending_topics(limit=12)
    topics = sorted(topics, key=lambda topic: _topic_score(topic, interest_terms), reverse=True)

    ranked_posts = build_twitter_feed(request)[:18]
    serialized_posts = PostSerializer(
        ranked_posts,
        many=True,
        context={
            'request': request,
            '_post_list': ranked_posts,
            '_author_summary_only': True,
        },
    ).data

    topic_items = [
        {
            'id': f"topic-{topic.get('topic')}-{index}",
            'type': 'topic',
            'topic': topic,
        }
        for index, topic in enumerate(topics)
    ]
    post_items = [
        {
            'id': f"post-{post.get('id')}",
            'type': 'post',
            'post': post,
        }
        for post in serialized_posts
    ]

    items = []
    topic_queue = list(topic_items)
    post_queue = list(post_items)
    pattern = ('topic', 'post', 'post')

    while len(items) < limit and (topic_queue or post_queue):
        for item_type in pattern:
            if item_type == 'topic' and topic_queue:
                items.append(topic_queue.pop(0))
            elif item_type == 'post' and post_queue:
                items.append(post_queue.pop(0))
            if len(items) >= limit:
                break
        if not topic_queue and not post_queue:
            break

    payload = {
        'tab': 'for_you',
        'items': items,
        'topics': topics[:12],
        'posts': serialized_posts[:18],
    }
    cache.set(cache_key, payload, 45)
    return payload


class ExploreTabView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, tab):
        normalized = (tab or '').strip().lower().replace('-', '_')
        if normalized not in EXPLORE_TABS:
            return Response({'detail': 'Unknown explore tab.'}, status=404)

        try:
            limit = min(max(int(request.query_params.get('limit', 18)), 1), 40)
        except (TypeError, ValueError):
            limit = 18

        if normalized == 'for_you':
            return Response(_build_explore_for_you(request, limit=limit))

        if normalized == 'trending':
            return Response({
                'tab': 'trending',
                'topics': build_trending_topics(limit=limit),
            })

        clusters = _build_clusters(request, limit=min(limit, 24), section=normalized)
        return Response({
            'tab': normalized,
            'clusters': clusters,
        })
