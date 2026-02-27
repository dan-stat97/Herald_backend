from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Post
from users.models import User as UserProfile
from django.shortcuts import get_object_or_404
from posts.models import Post
from .models import Post, Comment
from .serializers import CommentSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        post_id = self.request.data.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        user = UserProfile.objects.get(user_id=self.request.user)
        serializer.save(post=post, author=user)

    def get_queryset(self):
        post_id = self.request.query_params.get('post_id')
        if post_id:
            return self.queryset.filter(post__id=post_id)
        return self.queryset
