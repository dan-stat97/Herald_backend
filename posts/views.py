
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Post
from .serializers import PostSerializer, PostCreateSerializer
from users.models import User as UserProfile

class PostViewSet(viewsets.ModelViewSet):
	queryset = Post.objects.all().order_by('-created_at')
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [filters.OrderingFilter, filters.SearchFilter]
	ordering_fields = ['created_at', 'likes_count', 'comments_count', 'shares_count']
	search_fields = ['content']

	def get_serializer_class(self):
		if self.action in ['create', 'update', 'partial_update']:
			return PostCreateSerializer
		return PostSerializer

	def perform_create(self, serializer):
		serializer.save(author_id=UserProfile.objects.get(user_id=self.request.user))

	@action(detail=False, methods=['get'])
	def my(self, request):
		posts = Post.objects.filter(author_id__user_id=request.user)
		page = self.paginate_queryset(posts)
		if page is not None:
			serializer = PostSerializer(page, many=True)
			return self.get_paginated_response(serializer.data)
		serializer = PostSerializer(posts, many=True)
		return Response(serializer.data)
