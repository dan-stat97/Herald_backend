from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from users.models import User as UserProfile
from django.shortcuts import get_object_or_404
from .models import Post, Comment
from .serializers import CommentSerializer
from core.pagination import StandardPagination

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id') or self.request.data.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        user = UserProfile.objects.get(user_id=self.request.user)
        serializer.save(post=post, author=user)
        post.comments_count = max(0, (post.comments_count or 0) + 1)
        post.save(update_fields=['comments_count', 'updated_at'])

    def get_queryset(self):
        post_id = self.kwargs.get('post_id') or self.request.query_params.get('post_id')
        if post_id:
            return self.queryset.filter(post__id=post_id)
        return self.queryset

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        post = comment.post
        response = super().destroy(request, *args, **kwargs)
        post.comments_count = max(0, (post.comments_count or 0) - 1)
        post.save(update_fields=['comments_count', 'updated_at'])
        return response

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        comment.likes_count = max(0, (comment.likes_count or 0) + 1)
        comment.save(update_fields=['likes_count', 'updated_at'])
        return Response({'success': True, 'likes_count': comment.likes_count})
