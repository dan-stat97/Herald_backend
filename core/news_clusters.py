import math
import re
from collections import Counter, defaultdict
from datetime import timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import NewsArticle, NewsBookmark, NewsLike
from posts.models import Post
from users.models import User as UserProfile

HASHTAG_PATTERN = re.compile(r'#([A-Za-z0-9_]+)')
WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9']+")
STOP_WORDS = {
    'about', 'after', 'again', 'against', 'almost', 'also', 'among', 'because', 'been', 'before', 'being',
    'between', 'could', 'every', 'from', 'have', 'having', 'herald', 'into', 'just', 'more', 'most', 'news',
    'only', 'other', 'over', 'said', 'same', 'some', 'such', 'than', 'that', 'their', 'there', 'these', 'they',
    'this', 'those', 'today', 'under', 'very', 'what', 'when', 'where', 'which', 'while', 'with', 'would',
    'your', 'loveworld', 'healing', 'school', 'christian', 'external', 'social', 'media'
}


def _clean_token(token):
    token = (token or '').strip().lower().replace('-', '_')
    return token.strip('_')


def _display_topic(topic):
    topic = (topic or '').replace('_', ' ').strip()
    return ' '.join(word.capitalize() for word in topic.split())


def _article_source_type(article):
    category = (article.category or '').lower()
    if 'loveworld' in category:
        return 'loveworld'
    if 'healing' in category:
        return 'healing_school'
    if 'external' in category or 'christian' in category:
        return 'external'
    return 'herald'


def _article_source(article):
    source_type = _article_source_type(article)
    if source_type == 'loveworld':
        return 'Loveworld'
    if source_type == 'healing_school':
        return 'Healing School'
    if source_type == 'external':
        return 'External'
    return 'Herald Social'


def _article_summary(article):
    content = (article.content or '').strip()
    if not content:
        return None
    return content[:220] + ('...' if len(content) > 220 else '')


def _serialize_article(article, request=None):
    is_liked = False
    is_bookmarked = False
    if request and request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            is_liked = NewsLike.objects.filter(article=article, user=profile).exists()
            is_bookmarked = NewsBookmark.objects.filter(article=article, user=profile).exists()
        except Exception:
            pass

    return {
        'id': str(article.id),
        'title': article.title,
        'summary': _article_summary(article),
        'content': article.content,
        'source': _article_source(article),
        'source_type': _article_source_type(article),
        'image_url': article.image_url,
        'external_url': article.source_url,
        'published_at': article.created_at.isoformat(),
        'likes_count': article.likes_count,
        'is_liked': is_liked,
        'is_bookmarked': is_bookmarked,
        'category': article.category,
    }


def _keyword_tokens(text):
    tokens = []
    for raw in WORD_PATTERN.findall(text or ''):
        token = _clean_token(raw)
        if len(token) < 4 or token in STOP_WORDS:
            continue
        tokens.append(token)
    return tokens


def _build_topic_counter(post_limit=1200):
    cutoff = timezone.now() - timedelta(days=14)
    posts = Post.objects.filter(created_at__gte=cutoff).order_by('-created_at').values_list('content', flat=True)[:post_limit]

    counter = Counter()
    for content in posts:
        if not content:
            continue
        hashtags = [_clean_token(tag) for tag in HASHTAG_PATTERN.findall(content)]
        counter.update(tag for tag in hashtags if tag)
        counter.update(tag for tag in hashtags if tag)
        counter.update(_keyword_tokens(content))
    return counter


def _article_topic_candidates(article):
    candidates = []
    candidates.extend(_clean_token(tag) for tag in HASHTAG_PATTERN.findall(article.title or ''))
    candidates.extend(_clean_token(tag) for tag in HASHTAG_PATTERN.findall(article.content or ''))
    candidates.extend(_keyword_tokens(article.title or ''))
    candidates.extend(_keyword_tokens(article.category or ''))
    if article.category:
        candidates.append(_clean_token(article.category))

    ordered = []
    seen = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered[:8]


def _select_topic(article, topic_counter):
    candidates = _article_topic_candidates(article)
    if not candidates:
        fallback = _clean_token(article.category or 'news') or 'news'
        return fallback, topic_counter.get(fallback, 0)

    best_topic = candidates[0]
    best_score = -1
    for candidate in candidates:
        score = topic_counter.get(candidate, 0)
        if candidate == _clean_token(article.category or ''):
            score += 1
        if score > best_score:
            best_topic = candidate
            best_score = score
    return best_topic, max(best_score, 0)


def _build_clusters(request, limit=12, article_limit=80):
    topic_counter = _build_topic_counter()
    articles = list(NewsArticle.objects.all().order_by('-created_at')[:article_limit])

    if not articles:
        return []

    buckets = defaultdict(list)
    topic_meta = {}
    now = timezone.now()

    for article in articles:
        topic, post_count = _select_topic(article, topic_counter)
        buckets[topic].append(article)
        topic_meta[topic] = {
            'topic': topic,
            'display_name': _display_topic(topic),
            'tag': f'#{topic}',
            'posts_count': post_count,
        }

    clusters = []
    for topic, grouped_articles in buckets.items():
        grouped_articles.sort(key=lambda item: item.created_at, reverse=True)
        hero = grouped_articles[0]
        latest_seconds = max((now - hero.created_at).total_seconds(), 60)
        freshness_bonus = 1 / math.log(latest_seconds + 10, 10)
        score = topic_meta[topic]['posts_count'] * 3 + len(grouped_articles) * 4 + hero.likes_count + freshness_bonus
        clusters.append({
            'id': topic,
            'topic': topic,
            'display_name': topic_meta[topic]['display_name'],
            'tag': topic_meta[topic]['tag'],
            'posts_count': topic_meta[topic]['posts_count'],
            'articles_count': len(grouped_articles),
            'score': round(score, 2),
            'summary': _article_summary(hero),
            'latest_published_at': hero.created_at.isoformat(),
            'hero_article': _serialize_article(hero, request),
            'articles': [_serialize_article(article, request) for article in grouped_articles[:4]],
            'sources': sorted({item['source'] for item in [_serialize_article(article, request) for article in grouped_articles[:4]]}),
        })

    clusters.sort(key=lambda item: (item['score'], item['latest_published_at']), reverse=True)
    return clusters[:limit]


def _related_posts_for_topic(topic, limit=5):
    queries = [Q(content__icontains=f'#{topic}'), Q(content__icontains=topic.replace('_', ' '))]
    queryset = Post.objects.filter(queries[0] | queries[1]).select_related('author_id').order_by('-created_at')[:limit]
    data = []
    for post in queryset:
        data.append({
            'id': str(post.id),
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'shares_count': post.shares_count,
            'author': {
                'id': str(post.author_id.id) if post.author_id_id else None,
                'username': getattr(post.author_id, 'username', None),
                'display_name': getattr(post.author_id, 'display_name', None),
                'avatar_url': getattr(post.author_id, 'avatar_url', None),
            },
        })
    return data


class NewsClustersView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 12)), 24)
        search = (request.query_params.get('search') or '').strip().lower()
        clusters = _build_clusters(request, limit=limit)
        if search:
            filtered = []
            for cluster in clusters:
                haystack = ' '.join([
                    cluster['topic'],
                    cluster['display_name'],
                    cluster.get('summary') or '',
                    ' '.join(article['title'] for article in cluster['articles']),
                ]).lower()
                if search in haystack:
                    filtered.append(cluster)
            clusters = filtered
        return Response(clusters)


class NewsArticleContextView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, article_id):
        article = get_object_or_404(NewsArticle, id=article_id)
        topic_counter = _build_topic_counter()
        topic, posts_count = _select_topic(article, topic_counter)

        related_q = Q(title__icontains=topic.replace('_', ' ')) | Q(content__icontains=topic.replace('_', ' '))
        if article.category:
            related_q |= Q(category__icontains=article.category)

        related_articles = [
            _serialize_article(item, request)
            for item in NewsArticle.objects.filter(related_q).exclude(id=article.id).order_by('-created_at')[:6]
        ]

        return Response({
            'article': _serialize_article(article, request),
            'topic': {
                'id': topic,
                'topic': topic,
                'display_name': _display_topic(topic),
                'tag': f'#{topic}',
                'posts_count': posts_count,
                'articles_count': len(related_articles) + 1,
            },
            'related_articles': related_articles,
            'related_posts': _related_posts_for_topic(topic),
        })
