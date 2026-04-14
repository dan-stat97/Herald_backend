
import math

from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django.core.cache import cache
from django.db.models import F
from .models import Post, PostLike, PostRepost, PostBookmark
from .serializers import PostSerializer, PostCreateSerializer
from .ranking import rank_feed_posts
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
		"""Serve a ranked home feed similar to X's recommendation blend."""
		try:
			queryset = self.filter_queryset(self.get_queryset())
			sort = request.query_params.get('sort')
			manual_sort = bool(sort and sort != '-created_at')
			search = request.query_params.get('search')
			try:
				page_number = max(int(request.query_params.get('page', 1)), 1)
			except (TypeError, ValueError):
				page_number = 1
			try:
				request_limit = max(int(request.query_params.get('limit', 20)), 1)
			except (TypeError, ValueError):
				request_limit = 20

			is_default_feed = not manual_sort and not search
			cache_key = None
			user_scope = None
			if is_default_feed:
				user_scope = f"user:{request.user.id}" if getattr(request.user, 'is_authenticated', False) else 'anon'
				cache_key = f"feed:page:{page_number}:limit:{min(request_limit, 100)}:{user_scope}:v2"
				cached_payload = cache.get(cache_key)
				if cached_payload is not None:
					return Response(cached_payload)

			candidate_limit = min(max(request_limit, 20) * 5, 180)

			if manual_sort or search:
				ranked_items = queryset
			else:
				ranked_ids_cache_key = f"feed:ranked-ids:{user_scope}:limit:{candidate_limit}:v1"
				ranked_ids = cache.get(ranked_ids_cache_key)
				if ranked_ids is None:
					ranked_items = rank_feed_posts(queryset, request, candidate_limit=candidate_limit)
					ranked_ids = [item.id for item in ranked_items]
					cache.set(ranked_ids_cache_key, ranked_ids, 30)

				start = (page_number - 1) * request_limit
				end = start + request_limit
				page_ids = ranked_ids[start:end]
				if page_ids:
					page_map = {
						post.id: post
						for post in queryset.filter(id__in=page_ids)
					}
					page_items = [page_map[post_id] for post_id in page_ids if post_id in page_map]
				else:
					page_items = []

				serializer = self.get_serializer(
					page_items,
					many=True,
					context={**self.get_serializer_context(), '_post_list': page_items},
				)
				payload = {
					'data': serializer.data,
					'pagination': {
						'page': page_number,
						'limit': request_limit,
						'total': len(ranked_ids),
						'total_pages': math.ceil(len(ranked_ids) / request_limit) if request_limit else 0,
					},
				}
				if cache_key:
					cache.set(cache_key, payload, 30)
				return Response(payload)

			page = self.paginate_queryset(ranked_items)
			if page is not None:
				page_items = list(page)
				serializer = self.get_serializer(page_items, many=True, context={**self.get_serializer_context(), '_post_list': page_items})
				response = self.get_paginated_response(serializer.data)
				if cache_key:
					cache.set(cache_key, response.data, 30)
				return response
			items = list(ranked_items)
			serializer = self.get_serializer(items, many=True, context={**self.get_serializer_context(), '_post_list': items})
			payload = serializer.data
			if cache_key:
				cache.set(cache_key, payload, 30)
			return Response(payload)
		except Exception as e:
			print(f"Error listing posts: {e}")
			# Return empty paginated payload instead of 500 error
			return Response({'data': [], 'pagination': {'page': 1, 'limit': 20, 'total': 0, 'total_pages': 0}})

	def get_serializer_class(self):
		if self.action in ['create', 'update', 'partial_update']:
			return PostCreateSerializer
		return PostSerializer

	def retrieve(self, request, *args, **kwargs):
		instance = self.get_object()
		Post.objects.filter(pk=instance.pk).update(views_count=F('views_count') + 1)
		instance.refresh_from_db()
		serializer = self.get_serializer(instance, context={**self.get_serializer_context(), '_post_list': [instance]})
		return Response(serializer.data)

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		instance = serializer.instance
		if instance is None:
			return Response(serializer.data, status=status.HTTP_200_OK)
		instance = Post.objects.select_related('author_id', 'author_id__user_id').get(pk=instance.pk)
		response_serializer = PostSerializer(instance, context={**self.get_serializer_context(), '_post_list': [instance]})
		headers = self.get_success_headers(response_serializer.data)
		return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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
			page_items = list(page)
			serializer = PostSerializer(page_items, many=True, context={**self.get_serializer_context(), '_post_list': page_items})
			return self.get_paginated_response(serializer.data)
		items = list(posts)
		serializer = PostSerializer(items, many=True, context={**self.get_serializer_context(), '_post_list': items})
		return Response(serializer.data)

	@action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
	def trending(self, request):
		"""Posts sorted by engagement (likes + comments + shares) in the last 48 hours."""
		from django.utils import timezone
		from datetime import timedelta
		from django.db.models import F, ExpressionWrapper, IntegerField

		limit = min(int(request.query_params.get('limit', 20)), 100)
		cache_key = f"posts:trending:limit:{limit}:v2"
		cached_payload = cache.get(cache_key)
		if cached_payload is not None:
			return Response(cached_payload)
		cutoff = timezone.now() - timedelta(hours=48)

		def _fetch(extra_filter=None):
			qs = (
				Post.objects
				.select_related('author_id', 'author_id__user_id')
				.annotate(
					engagement=ExpressionWrapper(
						F('likes_count') + F('comments_count') + F('shares_count'),
						output_field=IntegerField(),
					)
				)
				.order_by('-engagement', '-created_at')
			)
			if extra_filter:
				qs = qs.filter(**extra_filter)
			# Evaluate to list immediately — avoids calling .exists() on a sliced
			# queryset which would fire a second full annotated query.
			return list(qs[:limit])

		post_items = _fetch({'created_at__gte': cutoff})
		if not post_items:
			post_items = _fetch()

		serializer = PostSerializer(post_items, many=True, context={**self.get_serializer_context(), '_post_list': post_items})
		payload = {'data': serializer.data, 'pagination': {'page': 1, 'limit': limit, 'total': len(post_items), 'total_pages': 1}}
		cache.set(cache_key, payload, 30)
		return Response(payload)

	@action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
	def following(self, request):
		"""Posts from users the authenticated user follows."""
		from core.models import Follow, Profiles

		limit = min(int(request.query_params.get('limit', 20)), 100)
		page = max(int(request.query_params.get('page', 1)), 1)
		cache_key = f"posts:following:user:{request.user.id}:page:{page}:limit:{limit}:v2"
		cached_payload = cache.get(cache_key)
		if cached_payload is not None:
			return Response(cached_payload)
		offset = (page - 1) * limit
		default_usernames = ['heraldnews', 'heraldtoday', 'heraldworlddesk', 'heraldprayerdesk', 'heraldworship']

		try:
			profile = UserProfile.objects.get(user_id=request.user)
		except UserProfile.DoesNotExist:
			payload = {'data': [], 'pagination': {'page': 1, 'limit': limit, 'has_more': False}}
			cache.set(cache_key, payload, 20)
			return Response(payload)

		# Look up legacy profile without writing (ensure_legacy_profile does a
		# get_or_create + possible UPDATE on every request — too expensive here).
		legacy = Profiles.objects.filter(user_id=profile.user_id_id).first()

		# Resolve followed users' auth IDs in one subquery instead of two queries.
		if legacy:
			following_auth_ids = list(
				Profiles.objects.filter(
					id__in=Follow.objects.filter(follower_id=legacy.id).values('following_id')
				).values_list('user_id', flat=True)
			)
		else:
			following_auth_ids = []

		if not following_auth_ids:
			default_ids = list(
				UserProfile.objects.filter(username__in=default_usernames)
				.exclude(id=profile.id)
				.values_list('id', flat=True)
			)
			if not default_ids:
				payload = {
					'data': [],
					'pagination': {'page': 1, 'limit': limit, 'has_more': False},
					'message': 'Follow some users to see their posts here.',
				}
				cache.set(cache_key, payload, 20)
				return Response(payload)

			posts_qs = (
				Post.objects
				.select_related('author_id', 'author_id__user_id')
				.filter(author_id__id__in=default_ids)
				.order_by('-created_at')
			)
			# Fetch limit+1 to determine has_more without a COUNT(*) query
			post_items = list(posts_qs[offset:offset + limit + 1])
			has_more = len(post_items) > limit
			post_items = post_items[:limit]
			serializer = PostSerializer(post_items, many=True, context={**self.get_serializer_context(), '_post_list': post_items})
			payload = {
				'data': serializer.data,
				'pagination': {'page': page, 'limit': limit, 'has_more': has_more},
				'message': 'Showing official Herald accounts until you follow people.',
				'is_default_feed': True,
			}
			cache.set(cache_key, payload, 20)
			return Response(payload)

		posts_qs = (
			Post.objects
			.select_related('author_id', 'author_id__user_id')
			.filter(author_id__user_id_id__in=following_auth_ids)
			.order_by('-created_at')
		)
		# Fetch limit+1 to determine has_more without a COUNT(*) query
		post_items = list(posts_qs[offset:offset + limit + 1])
		has_more = len(post_items) > limit
		post_items = post_items[:limit]
		serializer = PostSerializer(post_items, many=True, context={**self.get_serializer_context(), '_post_list': post_items})
		payload = {
			'data': serializer.data,
			'pagination': {'page': page, 'limit': limit, 'has_more': has_more},
		}
		cache.set(cache_key, payload, 20)
		return Response(payload)
