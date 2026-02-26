# core/comments_views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Comment, Posts, Profiles
from .serializers import CommentSerializer
from .pagination import StandardPagination
import uuid

class CommentViewSet(viewsets.ModelViewSet):
    """
    Comments API
    GET    /api/v1/comments/?post_id=xxx
    POST   /api/v1/comments/
    GET    /api/v1/comments/{id}/
    PUT    /api/v1/comments/{id}/
    DELETE /api/v1/comments/{id}/
    """
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by post
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        # Filter by author
        author_id = self.request.query_params.get('author_id')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        return queryset
    
    def perform_create(self, serializer):
        profile = Profiles.objects.get(user_id=self.request.user.id)
        serializer.save(
            id=uuid.uuid4(),
            author=profile
        )
        
        # Update post comments count
        post_id = self.request.data.get('post_id')
        if post_id:
            try:
                post = Posts.objects.get(id=post_id)
                post.replies_count = (post.replies_count or 0) + 1
                post.save()
            except Posts.DoesNotExist:
                pass
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a comment"""
        comment = self.get_object()
        comment.likes_count = (comment.likes_count or 0) + 1
        comment.save()
        return Response({
            'success': True,
            'likes_count': comment.likes_count
        })
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a comment"""
        comment = self.get_object()
        comment.likes_count = max(0, (comment.likes_count or 0) - 1)
        comment.save()
        return Response({
            'success': True,
            'likes_count': comment.likes_count
        })
    
    @action(detail=False, methods=['get'])
    def for_post(self, request):
        """Get comments for a specific post with pagination"""
        post_id = request.query_params.get('post_id')
        if not post_id:
            return Response({'error': 'post_id required'}, status=400)
        
        queryset = self.get_queryset().filter(post_id=post_id)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)