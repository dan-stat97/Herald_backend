from rest_framework import status, permissions, views
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Post
from users.models import User as UserProfile
from django.shortcuts import get_object_or_404
from posts.models import Post
from django.db import IntegrityError

# Dummy PostInteraction model for demonstration (replace with your actual model)
from django.db import models
class PostInteraction(models.Model):
    id = models.UUIDField(primary_key=True, default=models.UUIDField, editable=False)
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=[('like', 'Like'), ('share', 'Share'), ('bookmark', 'Bookmark')])
    created_at = models.DateTimeField(auto_now_add=True)

# Like, Unlike, Share, Bookmark API views
class PostLikeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        user = UserProfile.objects.get(user_id=request.user)
        try:
            PostInteraction.objects.create(post_id=post, user_id=user, interaction_type='like')
            post.likes_count += 1
            post.save()
        except IntegrityError:
            return Response({'error': 'Already liked'}, status=409)
        return Response({'success': True, 'likes_count': post.likes_count})
    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        user = UserProfile.objects.get(user_id=request.user)
        interaction = PostInteraction.objects.filter(post_id=post, user_id=user, interaction_type='like').first()
        if interaction:
            interaction.delete()
            post.likes_count = max(0, post.likes_count - 1)
            post.save()
        return Response({'success': True, 'likes_count': post.likes_count})

class PostShareView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        user = UserProfile.objects.get(user_id=request.user)
        PostInteraction.objects.create(post_id=post, user_id=user, interaction_type='share')
        post.shares_count += 1
        post.save()
        return Response({'success': True, 'shares_count': post.shares_count})

class PostBookmarkView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        user = UserProfile.objects.get(user_id=request.user)
        PostInteraction.objects.get_or_create(post_id=post, user_id=user, interaction_type='bookmark')
        return Response({'success': True})
