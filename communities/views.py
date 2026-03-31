from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db.models import Q
from .models import Community, CommunityMember, CommunityPost, CommunityPostLike
from users.models import User


def _get_profile(auth_user):
    return User.objects.get(user_id=auth_user)


def _serialize_community(c, user_community_ids):
    return {
        'id': str(c.id),
        'name': c.name,
        'description': c.description,
        'category': c.category,
        'image_url': c.image_url,
        'member_count': c.member_count,
        'is_private': c.is_private,
        'is_member': c.id in user_community_ids,
        'created_by': str(c.created_by_id),
        'created_at': c.created_at.isoformat(),
    }


def _serialize_post(p, liked_ids=None):
    return {
        'id': str(p.id),
        'content': p.content,
        'media_url': p.media_url,
        'media_type': p.media_type,
        'likes_count': p.likes_count,
        'comments_count': p.comments_count,
        'is_liked': (p.id in liked_ids) if liked_ids is not None else False,
        'created_at': p.created_at.isoformat(),
        'author': {
            'id': str(p.author.id),
            'username': p.author.username,
            'display_name': p.author.display_name,
            'avatar_url': p.author.avatar_url,
            'is_verified': p.author.is_verified,
            'tier': p.author.tier,
        },
    }


class CommunityListCreateView(views.APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        tab = request.query_params.get('tab', 'discover')
        search = request.query_params.get('search', '').strip()

        qs = Community.objects.all()

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

        # Resolve current user profile once
        profile = None
        user_community_ids = set()
        if request.user.is_authenticated:
            try:
                profile = _get_profile(request.user)
                user_community_ids = set(
                    CommunityMember.objects.filter(user=profile).values_list('community_id', flat=True)
                )
            except User.DoesNotExist:
                pass

        if tab == 'joined':
            if profile:
                qs = qs.filter(members__user=profile)
            else:
                qs = Community.objects.none()
        elif tab == 'trending':
            qs = qs.order_by('-member_count')
        else:
            qs = qs.order_by('-created_at')

        data = [_serialize_community(c, user_community_ids) for c in qs[:50]]
        return Response(data)

    def post(self, request):
        try:
            profile = _get_profile(request.user)
        except User.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=404)

        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'Name is required'}, status=400)

        community = Community.objects.create(
            name=name,
            description=request.data.get('description', ''),
            category=request.data.get('category', 'general'),
            is_private=request.data.get('is_private', False),
            image_url=request.data.get('image_url'),
            created_by=profile,
            member_count=1,
        )
        # Auto-join creator as admin
        CommunityMember.objects.create(community=community, user=profile, role='admin')

        return Response(_serialize_community(community, {community.id}), status=201)


class CommunityDetailView(views.APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        user_community_ids = set()
        if request.user.is_authenticated:
            try:
                profile = _get_profile(request.user)
                if CommunityMember.objects.filter(community=community, user=profile).exists():
                    user_community_ids.add(community.id)
            except User.DoesNotExist:
                pass

        return Response(_serialize_community(community, user_community_ids))

    def patch(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
            profile = _get_profile(request.user)
        except (Community.DoesNotExist, User.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        is_admin = CommunityMember.objects.filter(
            community=community, user=profile, role='admin'
        ).exists()
        if community.created_by != profile and not is_admin:
            return Response({'error': 'Permission denied'}, status=403)

        for field in ('name', 'description', 'category', 'image_url', 'is_private'):
            if field in request.data:
                setattr(community, field, request.data[field])
        community.save()

        return Response(_serialize_community(community, {community.id}))


class CommunityPostsView(views.APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        posts = CommunityPost.objects.filter(community=community).select_related('author')[:30]

        liked_ids = set()
        if request.user.is_authenticated:
            try:
                profile = _get_profile(request.user)
                liked_ids = set(
                    CommunityPostLike.objects.filter(
                        user=profile, post__community=community
                    ).values_list('post_id', flat=True)
                )
            except User.DoesNotExist:
                pass

        return Response([_serialize_post(p, liked_ids) for p in posts])

    def post(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        try:
            profile = _get_profile(request.user)
        except User.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=404)

        if not CommunityMember.objects.filter(community=community, user=profile).exists():
            return Response({'error': 'You must be a member to post'}, status=403)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Content is required'}, status=400)

        post = CommunityPost.objects.create(
            community=community,
            author=profile,
            content=content,
            media_url=request.data.get('media_url'),
            media_type=request.data.get('media_type'),
        )
        return Response(_serialize_post(post, set()), status=201)


class CommunityPostLikeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, community_id, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id, community_id=community_id)
            profile = _get_profile(request.user)
        except (CommunityPost.DoesNotExist, User.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        _, created = CommunityPostLike.objects.get_or_create(post=post, user=profile)
        if created:
            post.likes_count = post.likes.count()
            post.save(update_fields=['likes_count'])
        return Response({'liked': True, 'likes_count': post.likes_count})

    def delete(self, request, community_id, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id, community_id=community_id)
            profile = _get_profile(request.user)
        except (CommunityPost.DoesNotExist, User.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        CommunityPostLike.objects.filter(post=post, user=profile).delete()
        post.likes_count = post.likes.count()
        post.save(update_fields=['likes_count'])
        return Response({'liked': False, 'likes_count': post.likes_count})


class CommunityMembersView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, community_id):
        try:
            Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        members = CommunityMember.objects.filter(
            community_id=community_id
        ).select_related('user').order_by('joined_at')[:100]

        data = [
            {
                'id': str(m.id),
                'role': m.role,
                'joined_at': m.joined_at.isoformat(),
                'user': {
                    'id': str(m.user.id),
                    'username': m.user.username,
                    'display_name': m.user.display_name,
                    'avatar_url': m.user.avatar_url,
                    'is_verified': m.user.is_verified,
                    'tier': m.user.tier,
                },
            }
            for m in members
        ]
        return Response(data)
