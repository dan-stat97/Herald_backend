from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import F
from .models import Post, Comment
from .serializers import CommentSerializer
from core.pagination import StandardPagination
from users.views import ensure_user_profile

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id') or self.request.data.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        user = ensure_user_profile(self.request.user)
        serializer.save(post=post, author=user)
        # Atomic increment — safe under concurrent requests
        Post.objects.filter(pk=post.pk).update(comments_count=F('comments_count') + 1)

    def get_queryset(self):
        post_id = self.kwargs.get('post_id') or self.request.query_params.get('post_id')
        if post_id:
            return Comment.objects.filter(post__id=post_id).select_related('author', 'author__user_id').order_by('created_at')
        return self.queryset

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        post = comment.post
        response = super().destroy(request, *args, **kwargs)
        # Atomic decrement, floor at 0
        Post.objects.filter(pk=post.pk).update(
            comments_count=F('comments_count') - 1
        )
        return response

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        Comment.objects.filter(pk=comment.pk).update(likes_count=F('likes_count') + 1)
        comment.refresh_from_db(fields=['likes_count'])
        return Response({'success': True, 'likes_count': comment.likes_count})
