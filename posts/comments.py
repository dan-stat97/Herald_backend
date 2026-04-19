from django.core.cache import cache
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.pagination import StandardPagination
from users.views import ensure_user_profile

from .cache_utils import bump_post_timeline_cache_version
from .models import Comment, CommentBookmark, CommentLike, CommentRepost, Post
from .serializers import CommentSerializer


def _comment_cache_version(post_id):
    key = f'post-comments-version:{post_id}'
    version = cache.get(key)
    if version is None:
        version = 1
        cache.set(key, version, 60 * 60)
    return version


def _bump_comment_cache_version(post_id):
    key = f'post-comments-version:{post_id}'
    try:
        version = cache.incr(key)
    except ValueError:
        version = 2
        cache.set(key, version, 60 * 60)
    return version


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id') or self.request.query_params.get('post_id')
        sort = (self.request.query_params.get('sort') or 'relevant').lower()
        base = Comment.objects.select_related('author', 'author__user_id', 'parent_comment').all()
        if sort == 'recent':
            ordering = ('-created_at',)
        elif sort == 'liked':
            ordering = ('-likes_count', '-created_at')
        else:
            ordering = ('-likes_count', '-replies_count', '-shares_count', '-created_at')
        if post_id:
            return base.filter(post__id=post_id).order_by(*ordering)
        return base.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id') or request.query_params.get('post_id')
        queryset = self.get_queryset()
        if not post_id:
            page = self.paginate_queryset(queryset)
            if page is not None:
                page_items = list(page)
                serializer = self.get_serializer(page_items, many=True, context={**self.get_serializer_context()})
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(list(queryset), many=True, context={**self.get_serializer_context()})
            return Response(serializer.data)

        try:
            page_number = max(int(request.query_params.get('page', 1)), 1)
        except (TypeError, ValueError):
            page_number = 1
        try:
            limit = min(max(int(request.query_params.get('limit', 20)), 1), 100)
        except (TypeError, ValueError):
            limit = 20

        cache_version = _comment_cache_version(post_id)
        sort = (request.query_params.get('sort') or 'relevant').lower()
        cache_key = f'post-comments:{post_id}:sort:{sort}:page:{page_number}:limit:{limit}:v{cache_version}'
        cached_payload = cache.get(cache_key)
        if cached_payload is not None:
            return Response(cached_payload)

        offset = (page_number - 1) * limit
        items = list(queryset[offset:offset + limit + 1])
        has_more = len(items) > limit
        page_items = items[:limit]
        serializer = self.get_serializer(page_items, many=True, context={**self.get_serializer_context()})
        payload = {
            'data': serializer.data,
            'pagination': {
                'page': page_number,
                'limit': limit,
                'has_more': has_more,
            },
        }
        cache.set(cache_key, payload, 30)
        return Response(payload)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Comment.objects.filter(pk=instance.pk).update(views_count=F('views_count') + 1)
        instance.views_count = (instance.views_count or 0) + 1
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id') or self.request.data.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        user = ensure_user_profile(self.request.user)
        parent_comment_id = serializer.validated_data.pop('parent_comment_id', None)
        parent_comment = None
        if parent_comment_id:
            parent_comment = get_object_or_404(Comment, id=parent_comment_id, post=post)

        serializer.save(post=post, author=user, parent_comment=parent_comment)
        Post.objects.filter(pk=post.pk).update(comments_count=F('comments_count') + 1)
        if parent_comment:
            Comment.objects.filter(pk=parent_comment.pk).update(replies_count=F('replies_count') + 1)
        _bump_comment_cache_version(post.id)
        bump_post_timeline_cache_version()

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        try:
            profile = ensure_user_profile(request.user)
        except Exception:
            raise PermissionDenied("Authentication required.")
        if comment.author != profile:
            raise PermissionDenied("You can only delete your own comments.")
        if getattr(profile, 'tier', 'free') == 'free':
            raise PermissionDenied("Comment deletion is available on pro plans only.")
        post = comment.post
        parent = comment.parent_comment
        response = super().destroy(request, *args, **kwargs)
        Post.objects.filter(pk=post.pk).update(comments_count=F('comments_count') - 1)
        if parent:
            Comment.objects.filter(pk=parent.pk).update(replies_count=F('replies_count') - 1)
        _bump_comment_cache_version(post.id)
        bump_post_timeline_cache_version()
        return response

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        try:
            profile = ensure_user_profile(request.user)
        except Exception:
            raise PermissionDenied("Authentication required.")
        _, created = CommentLike.objects.get_or_create(comment=comment, user=profile)
        if created:
            Comment.objects.filter(pk=comment.pk).update(likes_count=F('likes_count') + 1)
            _bump_comment_cache_version(comment.post_id)
        comment.refresh_from_db(fields=['likes_count'])
        return Response({'success': True, 'liked': True, 'likes_count': comment.likes_count})

    @action(detail=True, methods=['post', 'delete'])
    def unlike(self, request, pk=None):
        comment = self.get_object()
        try:
            profile = ensure_user_profile(request.user)
        except Exception:
            raise PermissionDenied("Authentication required.")
        deleted, _ = CommentLike.objects.filter(comment=comment, user=profile).delete()
        if deleted:
            Comment.objects.filter(pk=comment.pk).update(likes_count=F('likes_count') - 1)
            _bump_comment_cache_version(comment.post_id)
        comment.refresh_from_db(fields=['likes_count'])
        return Response({'success': True, 'liked': False, 'likes_count': comment.likes_count})

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        comment = self.get_object()
        try:
            profile = ensure_user_profile(request.user)
        except Exception:
            raise PermissionDenied("Authentication required.")
        _, created = CommentRepost.objects.get_or_create(comment=comment, user=profile)
        if created:
            Comment.objects.filter(pk=comment.pk).update(shares_count=F('shares_count') + 1)
            _bump_comment_cache_version(comment.post_id)
        comment.refresh_from_db(fields=['shares_count'])
        return Response({'success': True, 'reposted': True, 'shares_count': comment.shares_count})

    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        comment = self.get_object()
        try:
            profile = ensure_user_profile(request.user)
        except Exception:
            raise PermissionDenied("Authentication required.")
        _, created = CommentBookmark.objects.get_or_create(comment=comment, user=profile)
        if created:
            Comment.objects.filter(pk=comment.pk).update(bookmarks_count=F('bookmarks_count') + 1)
            _bump_comment_cache_version(comment.post_id)
        comment.refresh_from_db(fields=['bookmarks_count'])
        return Response({'success': True, 'bookmarked': True, 'bookmarks_count': comment.bookmarks_count})

    @action(detail=True, methods=['post', 'delete'])
    def unbookmark(self, request, pk=None):
        comment = self.get_object()
        try:
            profile = ensure_user_profile(request.user)
        except Exception:
            raise PermissionDenied("Authentication required.")
        deleted, _ = CommentBookmark.objects.filter(comment=comment, user=profile).delete()
        if deleted:
            Comment.objects.filter(pk=comment.pk).update(bookmarks_count=F('bookmarks_count') - 1)
            _bump_comment_cache_version(comment.post_id)
        comment.refresh_from_db(fields=['bookmarks_count'])
        return Response({'success': True, 'bookmarked': False, 'bookmarks_count': comment.bookmarks_count})
