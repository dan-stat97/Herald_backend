
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Post
from .serializers import PostSerializer, PostCreateSerializer
from users.models import User as UserProfile
from core.pagination import StandardPagination

class PostViewSet(viewsets.ModelViewSet):
	queryset = Post.objects.all().order_by('-created_at')
	permission_classes = [permissions.IsAuthenticated]
	pagination_class = StandardPagination
	filter_backends = [filters.OrderingFilter, filters.SearchFilter]
	ordering_fields = ['created_at', 'likes_count', 'comments_count', 'shares_count']
	search_fields = ['content']

	def get_permissions(self):
		# Feed endpoints are auth-optional; write operations remain protected.
		if self.action in ['list', 'retrieve']:
			return [permissions.AllowAny()]
		return [permission() for permission in self.permission_classes]

	def get_queryset(self):
		"""Optimize queryset with select_related to prevent N+1 queries"""
		try:
			queryset = Post.objects.select_related('author_id', 'author_id__user_id').all().order_by('-created_at')
			sort = self.request.query_params.get('sort')
			allowed_sort_fields = {'created_at', 'likes_count', 'comments_count', 'shares_count'}
			if sort and sort.lstrip('-') in allowed_sort_fields:
				queryset = queryset.order_by(sort)
			return queryset
		except Exception as e:
			# Fallback to basic queryset if select_related fails
			print(f"Error in get_queryset: {e}")
			queryset = Post.objects.all().order_by('-created_at')
			sort = self.request.query_params.get('sort')
			allowed_sort_fields = {'created_at', 'likes_count', 'comments_count', 'shares_count'}
			if sort and sort.lstrip('-') in allowed_sort_fields:
				queryset = queryset.order_by(sort)
			return queryset

	def list(self, request, *args, **kwargs):
		"""Override list to add error handling"""
		try:
			return super().list(request, *args, **kwargs)
		except Exception as e:
			print(f"Error listing posts: {e}")
			# Return empty paginated payload instead of 500 error
			return Response({'data': [], 'pagination': {'page': 1, 'limit': 20, 'total': 0, 'total_pages': 0}})

	def get_serializer_class(self):
		if self.action in ['create', 'update', 'partial_update']:
			return PostCreateSerializer
		return PostSerializer

	def perform_create(self, serializer):
		try:
			from django.db import transaction
			profile = UserProfile.objects.get(user_id=self.request.user)
			
			# Check for duplicate posts (same content from same user in last 5 seconds)
			from django.utils import timezone
			from datetime import timedelta
			recent_time = timezone.now() - timedelta(seconds=5)
			content = serializer.validated_data.get('content', '')
			
			duplicate_exists = Post.objects.filter(
				author_id=profile,
				content=content,
				created_at__gte=recent_time
			).exists()
			
			if duplicate_exists:
				# Return existing post instead of creating duplicate
				existing_post = Post.objects.filter(
					author_id=profile,
					content=content,
					created_at__gte=recent_time
				).first()
				serializer.instance = existing_post
				return
			
			# Use atomic transaction to prevent race conditions
			with transaction.atomic():
				post = serializer.save(author_id=profile)
				
				# Award 25 HTTN Points for creating a post
				from wallets.models import Wallet
				wallet = Wallet.objects.select_for_update().get(user_id=profile)
				wallet.httn_points += 25
				wallet.save(update_fields=['httn_points', 'updated_at'])
			
		except UserProfile.DoesNotExist:
			from rest_framework.exceptions import ValidationError
			raise ValidationError("User profile not found. Please complete your profile first.")

	@action(detail=True, methods=['post'])
	def like(self, request, pk=None):
		post = self.get_object()
		post.likes_count += 1
		post.save(update_fields=['likes_count', 'updated_at'])
		return Response({'success': True, 'likes_count': post.likes_count})

	@action(detail=True, methods=['delete', 'post'])
	def unlike(self, request, pk=None):
		post = self.get_object()
		post.likes_count = max(0, post.likes_count - 1)
		post.save(update_fields=['likes_count', 'updated_at'])
		return Response({'success': True, 'likes_count': post.likes_count})

	@action(detail=True, methods=['post'])
	def share(self, request, pk=None):
		post = self.get_object()
		post.shares_count += 1
		post.save(update_fields=['shares_count', 'updated_at'])
		return Response({'success': True, 'shares_count': post.shares_count})

	@action(detail=False, methods=['get'])
	def my(self, request):
		posts = Post.objects.filter(author_id__user_id=request.user)
		page = self.paginate_queryset(posts)
		if page is not None:
			serializer = PostSerializer(page, many=True)
			return self.get_paginated_response(serializer.data)
		serializer = PostSerializer(posts, many=True)
		return Response(serializer.data)
