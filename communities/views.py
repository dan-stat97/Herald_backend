from django.db import IntegrityError
from django.db.models import Q
from rest_framework import permissions, status, views
from rest_framework.response import Response

from .models import Community, CommunityMember, CommunityPost, CommunityPostLike
from users.models import User


def _get_profile(auth_user):
    profile, created = User.objects.get_or_create(
        user_id=auth_user,
        defaults={
            'username': auth_user.username,
            'display_name': auth_user.first_name or auth_user.username,
            'full_name': auth_user.get_full_name() or auth_user.username,
            'email': auth_user.email or '',
        },
    )

    updated_fields = []
    if not profile.username and auth_user.username:
        profile.username = auth_user.username
        updated_fields.append('username')
    if not profile.display_name:
        profile.display_name = auth_user.first_name or auth_user.username
        updated_fields.append('display_name')
    if not profile.full_name:
        profile.full_name = auth_user.get_full_name() or auth_user.username
        updated_fields.append('full_name')
    if not profile.email and auth_user.email:
        profile.email = auth_user.email
        updated_fields.append('email')

    if updated_fields:
        profile.save(update_fields=updated_fields + ['updated_at'])

    return profile


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


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

        profile = None
        user_community_ids = set()
        if request.user.is_authenticated:
            profile = _get_profile(request.user)
            user_community_ids = set(
                CommunityMember.objects.filter(user=profile).values_list('community_id', flat=True)
            )

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
        profile = _get_profile(request.user)

        name = (request.data.get('name') or '').strip()
        if not name:
            return Response({'error': 'Name is required'}, status=400)
        if len(name) > 200:
            return Response({'error': 'Name must be 200 characters or fewer'}, status=400)

        try:
            community = Community.objects.create(
                name=name,
                description=(request.data.get('description') or '').strip(),
                category=(request.data.get('category') or 'general').strip() or 'general',
                is_private=_coerce_bool(request.data.get('is_private', False)),
                image_url=(request.data.get('image_url') or None),
                created_by=profile,
                member_count=0,
            )
            CommunityMember.objects.get_or_create(community=community, user=profile, defaults={'role': 'admin'})
            community.member_count = community.members.count()
            community.save(update_fields=['member_count'])
        except IntegrityError:
            return Response({'error': 'A community with this configuration already exists or conflicts with existing data.'}, status=409)
        except Exception as exc:
            return Response({'error': f'Failed to create community: {exc}'}, status=500)

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
            profile = _get_profile(request.user)
            if CommunityMember.objects.filter(community=community, user=profile).exists():
                user_community_ids.add(community.id)

        return Response(_serialize_community(community, user_community_ids))

    def patch(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)

        is_admin = CommunityMember.objects.filter(
            community=community, user=profile, role='admin'
        ).exists()
        if community.created_by != profile and not is_admin:
            return Response({'error': 'Permission denied'}, status=403)

        for field in ('name', 'description', 'category', 'image_url', 'is_private'):
            if field in request.data:
                value = request.data[field]
                if field == 'is_private':
                    value = _coerce_bool(value)
                setattr(community, field, value)
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
            profile = _get_profile(request.user)
            liked_ids = set(
                CommunityPostLike.objects.filter(
                    user=profile, post__community=community
                ).values_list('post_id', flat=True)
            )

        return Response([_serialize_post(p, liked_ids) for p in posts])

    def post(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        profile = _get_profile(request.user)

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
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)

        _, created = CommunityPostLike.objects.get_or_create(post=post, user=profile)
        if created:
            post.likes_count = post.likes.count()
            post.save(update_fields=['likes_count'])
        return Response({'liked': True, 'likes_count': post.likes_count})

    def delete(self, request, community_id, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id, community_id=community_id)
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)

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
