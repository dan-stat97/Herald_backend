from django.db import IntegrityError
from django.db.models import Q
from rest_framework import permissions, status, views
from rest_framework.response import Response

from .models import Community, CommunityMember, CommunityPost, CommunityPostLike
from users.models import User


def _get_profile(auth_user):
    profile, _ = User.objects.get_or_create(
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


def _normalise_rules(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()][:10]
    if isinstance(value, str):
        parts = [part.strip() for part in value.splitlines()]
        return [part for part in parts if part][:10]
    return []


def _serialize_community(community, membership=None):
    member_role = None
    if isinstance(membership, CommunityMember):
        member_role = membership.role
    elif isinstance(membership, str):
        member_role = membership

    is_member = bool(member_role)
    is_admin = member_role == 'admin' or community.created_by_id == getattr(getattr(membership, 'user', None), 'id', None)

    return {
        'id': str(community.id),
        'name': community.name,
        'description': community.description,
        'category': community.category,
        'image_url': community.image_url,
        'rules': community.rules or [],
        'member_count': community.member_count,
        'posts_count': getattr(community, 'posts_count', None) or community.posts.count(),
        'is_private': community.is_private,
        'is_member': is_member,
        'member_role': member_role,
        'is_admin': member_role == 'admin',
        'is_moderator': member_role == 'moderator',
        'created_by': str(community.created_by_id),
        'created_at': community.created_at.isoformat(),
        'updated_at': community.updated_at.isoformat(),
    }


def _serialize_post(post, liked_ids=None):
    media_type = post.media_type or None
    return {
        'id': str(post.id),
        'content': post.content,
        'media_url': post.media_url,
        'media_type': media_type,
        'likes_count': post.likes_count,
        'comments_count': post.comments_count,
        'is_liked': (post.id in liked_ids) if liked_ids is not None else False,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat(),
        'author': {
            'id': str(post.author.id),
            'username': post.author.username,
            'display_name': post.author.display_name,
            'avatar_url': post.author.avatar_url,
            'is_verified': post.author.is_verified,
            'tier': post.author.tier,
        },
    }


class CommunityListCreateView(views.APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        tab = (request.query_params.get('tab') or 'discover').strip()
        search = (request.query_params.get('search') or '').strip()

        queryset = Community.objects.all().prefetch_related('posts')

        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))

        membership_map = {}
        profile = None
        if request.user.is_authenticated:
            profile = _get_profile(request.user)
            membership_map = {
                str(member.community_id): member.role
                for member in CommunityMember.objects.filter(user=profile).only('community_id', 'role')
            }

        if tab == 'joined':
            if profile:
                queryset = queryset.filter(members__user=profile)
            else:
                queryset = Community.objects.none()
        elif tab == 'trending':
            queryset = queryset.order_by('-member_count', '-updated_at')
        else:
            queryset = queryset.order_by('-updated_at', '-created_at')

        data = [_serialize_community(community, membership_map.get(str(community.id))) for community in queryset[:50]]
        return Response(data)

    def post(self, request):
        profile = _get_profile(request.user)

        name = (request.data.get('name') or '').strip()
        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        if len(name) > 200:
            return Response({'error': 'Name must be 200 characters or fewer'}, status=status.HTTP_400_BAD_REQUEST)

        rules = _normalise_rules(request.data.get('rules'))

        try:
            community = Community.objects.create(
                name=name,
                description=(request.data.get('description') or '').strip(),
                category=(request.data.get('category') or 'general').strip() or 'general',
                image_url=(request.data.get('image_url') or None),
                rules=rules,
                is_private=_coerce_bool(request.data.get('is_private', False)),
                created_by=profile,
                member_count=0,
            )
            CommunityMember.objects.get_or_create(community=community, user=profile, defaults={'role': 'admin'})
            community.member_count = community.members.count()
            community.save(update_fields=['member_count'])
        except IntegrityError:
            return Response({'error': 'A community with this configuration already exists or conflicts with existing data.'}, status=status.HTTP_409_CONFLICT)
        except Exception as exc:
            return Response({'error': f'Failed to create community: {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(_serialize_community(community, 'admin'), status=status.HTTP_201_CREATED)


class CommunityDetailView(views.APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def _get_membership(self, request, community):
        if not request.user.is_authenticated:
            return None
        profile = _get_profile(request.user)
        return CommunityMember.objects.filter(community=community, user=profile).first()

    def get(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=status.HTTP_404_NOT_FOUND)

        membership = self._get_membership(request, community)
        return Response(_serialize_community(community, membership))

    def patch(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        profile = _get_profile(request.user)
        membership = CommunityMember.objects.filter(community=community, user=profile).first()
        is_admin = membership and membership.role == 'admin'
        if community.created_by != profile and not is_admin:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        for field in ('name', 'description', 'category', 'image_url'):
            if field in request.data:
                value = request.data.get(field)
                if isinstance(value, str):
                    value = value.strip()
                setattr(community, field, value or None if field == 'image_url' else value)

        if 'is_private' in request.data:
            community.is_private = _coerce_bool(request.data.get('is_private'))
        if 'rules' in request.data:
            community.rules = _normalise_rules(request.data.get('rules'))

        if not (community.name or '').strip():
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)

        community.save()
        refreshed_membership = CommunityMember.objects.filter(community=community, user=profile).first()
        return Response(_serialize_community(community, refreshed_membership))


class CommunityPostsView(views.APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=status.HTTP_404_NOT_FOUND)

        posts = CommunityPost.objects.filter(community=community).select_related('author').order_by('-created_at')[:50]

        liked_ids = set()
        if request.user.is_authenticated:
            profile = _get_profile(request.user)
            liked_ids = set(
                CommunityPostLike.objects.filter(user=profile, post__community=community).values_list('post_id', flat=True)
            )

        return Response([_serialize_post(post, liked_ids) for post in posts])

    def post(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=status.HTTP_404_NOT_FOUND)

        profile = _get_profile(request.user)
        membership = CommunityMember.objects.filter(community=community, user=profile).first()
        if not membership:
            return Response({'error': 'You must be a member to post'}, status=status.HTTP_403_FORBIDDEN)

        content = (request.data.get('content') or '').strip()
        media_url = request.data.get('media_url') or None
        media_type = (request.data.get('media_type') or '').strip().lower() or None

        if not content and not media_url:
            return Response({'error': 'Content or media is required'}, status=status.HTTP_400_BAD_REQUEST)
        if media_type and media_type not in {'image', 'video'}:
            return Response({'error': 'media_type must be image or video'}, status=status.HTTP_400_BAD_REQUEST)

        post = CommunityPost.objects.create(
            community=community,
            author=profile,
            content=content,
            media_url=media_url,
            media_type=media_type,
        )
        return Response(_serialize_post(post, set()), status=status.HTTP_201_CREATED)


class CommunityPostLikeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, community_id, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id, community_id=community_id)
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

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
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

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
            return Response({'error': 'Community not found'}, status=status.HTTP_404_NOT_FOUND)

        members = CommunityMember.objects.filter(community_id=community_id).select_related('user').order_by('joined_at')[:100]
        data = [
            {
                'id': str(member.id),
                'role': member.role,
                'joined_at': member.joined_at.isoformat(),
                'user': {
                    'id': str(member.user.id),
                    'username': member.user.username,
                    'display_name': member.user.display_name,
                    'avatar_url': member.user.avatar_url,
                    'is_verified': member.user.is_verified,
                    'tier': member.user.tier,
                },
            }
            for member in members
        ]
        return Response(data)
