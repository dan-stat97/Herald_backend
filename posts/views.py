
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import F
from .models import Post, PostLike, PostRepost, PostBookmark
from .serializers import PostSerializer, PostCreateSerializer
from users.models import User as UserProfile
from users.views import ensure_user_profile
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

	def _get_profile(self, request):
		"""Return the users.User profile for the authenticated user."""
		return ensure_user_profile(request.user)

	@action(detail=True, methods=['post'])
	def like(self, request, pk=None):
		post = self.get_object()
		try:
			profile = self._get_profile(request)
		except UserProfile.DoesNotExist:
			return Response({'error': 'User profile not found'}, status=404)

		_, created = PostLike.objects.get_or_create(post=post, user=profile)
		if created:
			Post.objects.filter(pk=post.pk).update(likes_count=F('likes_count') + 1)
		post.refresh_from_db(fields=['likes_count'])
		return Response({'success': True, 'liked': True, 'likes_count': post.likes_count})

	@action(detail=True, methods=['delete', 'post'])
	def unlike(self, request, pk=None):
		post = self.get_object()
		try:
			profile = self._get_profile(request)
		except UserProfile.DoesNotExist:
			return Response({'error': 'User profile not found'}, status=404)

		deleted, _ = PostLike.objects.filter(post=post, user=profile).delete()
		if deleted:
			Post.objects.filter(pk=post.pk).update(likes_count=F('likes_count') - 1)
		post.refresh_from_db(fields=['likes_count'])
		return Response({'success': True, 'liked': False, 'likes_count': post.likes_count})

	@action(detail=True, methods=['post'])
	def share(self, request, pk=None):
		"""Repost / share a post — idempotent per user."""
		post = self.get_object()
		try:
			profile = self._get_profile(request)
		except UserProfile.DoesNotExist:
			return Response({'error': 'User profile not found'}, status=404)

		_, created = PostRepost.objects.get_or_create(post=post, user=profile)
		if created:
			Post.objects.filter(pk=post.pk).update(shares_count=F('shares_count') + 1)
		post.refresh_from_db(fields=['shares_count'])
		return Response({'success': True, 'reposted': True, 'shares_count': post.shares_count})

	@action(detail=True, methods=['post'])
	def bookmark(self, request, pk=None):
		post = self.get_object()
		try:
			profile = self._get_profile(request)
		except UserProfile.DoesNotExist:
			return Response({'error': 'User profile not found'}, status=404)

		_, created = PostBookmark.objects.get_or_create(post=post, user=profile)
		if created:
			Post.objects.filter(pk=post.pk).update(bookmarks_count=F('bookmarks_count') + 1)
		post.refresh_from_db(fields=['bookmarks_count'])
		return Response({'success': True, 'bookmarked': True, 'bookmarks_count': post.bookmarks_count})

	@action(detail=True, methods=['post', 'delete'])
	def unbookmark(self, request, pk=None):
		post = self.get_object()
		try:
			profile = self._get_profile(request)
		except UserProfile.DoesNotExist:
			return Response({'error': 'User profile not found'}, status=404)

		deleted, _ = PostBookmark.objects.filter(post=post, user=profile).delete()
		if deleted:
			Post.objects.filter(pk=post.pk).update(bookmarks_count=F('bookmarks_count') - 1)
		post.refresh_from_db(fields=['bookmarks_count'])
		return Response({'success': True, 'bookmarked': False, 'bookmarks_count': post.bookmarks_count})

	@action(detail=False, methods=['get'])
	def my(self, request):
		posts = Post.objects.filter(author_id__user_id=request.user)
		page = self.paginate_queryset(posts)
		if page is not None:
			serializer = PostSerializer(page, many=True)
			return self.get_paginated_response(serializer.data)
		serializer = PostSerializer(posts, many=True)
		return Response(serializer.data)

	@action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
	def trending(self, request):
		"""Posts sorted by engagement (likes + comments + shares) in the last 48 hours."""
		from django.utils import timezone
		from datetime import timedelta
		from django.db.models import F, ExpressionWrapper, IntegerField

		limit = min(int(request.query_params.get('limit', 20)), 100)
		cutoff = timezone.now() - timedelta(hours=48)

		posts = (
			Post.objects
			.select_related('author_id', 'author_id__user_id')
			.annotate(
				engagement=ExpressionWrapper(
					F('likes_count') + F('comments_count') + F('shares_count'),
					output_field=IntegerField(),
				)
			)
			.filter(created_at__gte=cutoff)
			.order_by('-engagement', '-created_at')[:limit]
		)

		# Fall back to all-time if last 48h is empty
		if not posts.exists():
			posts = (
				Post.objects
				.select_related('author_id', 'author_id__user_id')
				.annotate(
					engagement=ExpressionWrapper(
						F('likes_count') + F('comments_count') + F('shares_count'),
						output_field=IntegerField(),
					)
				)
				.order_by('-engagement', '-created_at')[:limit]
			)

		serializer = PostSerializer(posts, many=True)
		return Response({'data': serializer.data, 'pagination': {'page': 1, 'limit': limit, 'total': len(serializer.data), 'total_pages': 1}})

	@action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
	def following(self, request):
		"""Posts from users the authenticated user follows."""
		from core.models import Follow

		limit = min(int(request.query_params.get('limit', 20)), 100)
		page = max(int(request.query_params.get('page', 1)), 1)

		try:
			profile = UserProfile.objects.get(user_id=request.user)
			following_ids = list(
				Follow.objects.filter(follower_id=profile.id).values_list('following_id', flat=True)
			)
		except UserProfile.DoesNotExist:
			return Response({'data': [], 'pagination': {'page': 1, 'limit': limit, 'total': 0, 'total_pages': 0}})

		if not following_ids:
			# Not following anyone — return empty with a hint
			return Response({
				'data': [],
				'pagination': {'page': 1, 'limit': limit, 'total': 0, 'total_pages': 0},
				'message': 'Follow some users to see their posts here.',
			})

		posts_qs = (
			Post.objects
			.select_related('author_id', 'author_id__user_id')
			.filter(author_id__id__in=following_ids)
			.order_by('-created_at')
		)

		total = posts_qs.count()
		offset = (page - 1) * limit
		posts = posts_qs[offset:offset + limit]

		serializer = PostSerializer(posts, many=True)
		return Response({
			'data': serializer.data,
			'pagination': {
				'page': page,
				'limit': limit,
				'total': total,
				'total_pages': (total + limit - 1) // limit,
			},
		})
