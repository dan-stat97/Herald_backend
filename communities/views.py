from django.db import IntegrityError
from django.db.models import Q
from rest_framework import permissions, status, views
from rest_framework.response import Response

from .models import (
    Community, CommunityMember, CommunityPost, CommunityPostLike,
    CommunityPostComment, CommunityJoinRequest, CommunityInvite,
)
from users.models import User
from .notify import (
    notify_join_request_received, notify_join_request_reviewed,
    notify_post_liked, notify_post_commented,
    notify_invite_sent, notify_invite_responded,
)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _get_profile(auth_user):
    profile, _ = User.objects.get_or_create(
        user_id=auth_user,
        defaults={
            'username':     auth_user.username,
            'display_name': auth_user.first_name or auth_user.username,
            'full_name':    auth_user.get_full_name() or auth_user.username,
            'email':        auth_user.email or '',
        },
    )
    updated = []
    if not profile.username and auth_user.username:
        profile.username = auth_user.username; updated.append('username')
    if not profile.display_name:
        profile.display_name = auth_user.first_name or auth_user.username; updated.append('display_name')
    if not profile.full_name:
        profile.full_name = auth_user.get_full_name() or auth_user.username; updated.append('full_name')
    if not profile.email and auth_user.email:
        profile.email = auth_user.email; updated.append('email')
    if updated:
        profile.save(update_fields=updated + ['updated_at'])
    return profile


def _coerce_bool(value):
    if isinstance(value, bool): return value
    if isinstance(value, str): return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def _normalise_rules(value):
    if value is None: return []
    if isinstance(value, list):
        return [str(i).strip() for i in value if str(i).strip()][:10]
    if isinstance(value, str):
        return [p.strip() for p in value.splitlines() if p.strip()][:10]
    return []


def _serialize_community(community, membership=None, join_request_status=None, my_invite=None):
    member_role = None
    if isinstance(membership, CommunityMember):
        member_role = membership.role
    elif isinstance(membership, str):
        member_role = membership

    invite_status = None
    invite_id = None
    if isinstance(my_invite, CommunityInvite):
        invite_status = my_invite.status
        invite_id = str(my_invite.id)
    elif isinstance(my_invite, dict):
        invite_status = my_invite.get('status')
        invite_id = my_invite.get('id')
    elif isinstance(my_invite, str):
        invite_status = my_invite

    return {
        'id':                  str(community.id),
        'name':                community.name,
        'description':         community.description,
        'category':            community.category,
        'image_url':           community.image_url,
        'rules':               community.rules or [],
        'entry_question':      community.entry_question,
        'membership_type':     community.membership_type,
        'is_private':          community.is_private,
        'member_count':        community.member_count,
        'posts_count':         getattr(community, 'posts_count', None) or community.posts.count(),
        'is_member':           bool(member_role),
        'member_role':         member_role,
        'is_admin':            member_role == 'admin',
        'is_moderator':        member_role == 'moderator',
        'join_request_status': join_request_status,
        'my_invite_status':    invite_status,
        'my_invite_id':        invite_id,
        'created_by':          str(community.created_by_id),
        'created_at':          community.created_at.isoformat(),
        'updated_at':          community.updated_at.isoformat(),
    }


def _serialize_post(post, liked_ids=None, include_comments=False):
    data = {
        'id':             str(post.id),
        'content':        post.content,
        'media_url':      post.media_url,
        'media_type':     post.media_type or None,
        'likes_count':    post.likes_count,
        'comments_count': post.comments_count,
        'is_pinned':      post.is_pinned,
        'is_liked':       (post.id in liked_ids) if liked_ids is not None else False,
        'created_at':     post.created_at.isoformat(),
        'updated_at':     post.updated_at.isoformat(),
        'author': {
            'id':           str(post.author.id),
            'username':     post.author.username,
            'display_name': post.author.display_name,
            'avatar_url':   post.author.avatar_url,
            'is_verified':  post.author.is_verified,
            'tier':         post.author.tier,
        },
    }
    if include_comments:
        comments = post.comments.select_related('author').order_by('created_at')[:3]
        data['comments'] = [_serialize_comment(c) for c in comments]
    return data


def _serialize_comment(comment):
    return {
        'id':         str(comment.id),
        'content':    comment.content,
        'created_at': comment.created_at.isoformat(),
        'author': {
            'id':           str(comment.author.id),
            'username':     comment.author.username,
            'display_name': comment.author.display_name,
            'avatar_url':   comment.author.avatar_url,
            'is_verified':  comment.author.is_verified,
        },
    }


def _is_mod_or_admin(profile, community):
    m = CommunityMember.objects.filter(community=community, user=profile).first()
    return m and m.role in ('admin', 'moderator')


CATEGORIES = [
    'general', 'faith', 'worship', 'prayer', 'education', 'health',
    'arts', 'technology', 'sports', 'news', 'business', 'entertainment',
]


# ── Community list / create ───────────────────────────────────────────────────

class CommunityListCreateView(views.APIView):
    def get_permissions(self):
        return [permissions.AllowAny()] if self.request.method == 'GET' else [permissions.IsAuthenticated()]

    def get(self, request):
        tab    = (request.query_params.get('tab') or 'discover').strip()
        search = (request.query_params.get('search') or '').strip()
        cat    = (request.query_params.get('category') or '').strip()

        qs = Community.objects.all().prefetch_related('posts')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if cat and cat != 'all':
            qs = qs.filter(category=cat)

        membership_map = {}
        invite_map = {}
        profile = None
        if request.user.is_authenticated:
            profile = _get_profile(request.user)
            membership_map = {
                str(m.community_id): m.role
                for m in CommunityMember.objects.filter(user=profile).only('community_id', 'role')
            }
            invite_map = {
                str(inv.community_id): {'status': inv.status, 'id': str(inv.id)}
                for inv in CommunityInvite.objects.filter(
                    invited_user=profile, status=CommunityInvite.STATUS_PENDING
                ).only('community_id', 'status', 'id')
            }

        if tab == 'joined':
            qs = qs.filter(members__user=profile) if profile else Community.objects.none()
        elif tab == 'trending':
            qs = qs.order_by('-member_count', '-updated_at')
        else:
            qs = qs.order_by('-updated_at', '-created_at')

        data = [_serialize_community(c, membership_map.get(str(c.id)), my_invite=invite_map.get(str(c.id))) for c in qs[:50]]
        return Response({'results': data, 'categories': CATEGORIES})

    def post(self, request):
        profile = _get_profile(request.user)
        name = (request.data.get('name') or '').strip()
        if not name:
            return Response({'error': 'Name is required'}, status=400)
        if len(name) > 200:
            return Response({'error': 'Name must be 200 characters or fewer'}, status=400)

        mt = request.data.get('membership_type', 'open')
        if mt not in ('open', 'request', 'invite'):
            mt = 'open'

        try:
            community = Community.objects.create(
                name=name,
                description=(request.data.get('description') or '').strip() or None,
                category=(request.data.get('category') or 'general').strip() or 'general',
                image_url=request.data.get('image_url') or None,
                rules=_normalise_rules(request.data.get('rules')),
                is_private=mt != 'open',
                membership_type=mt,
                entry_question=(request.data.get('entry_question') or '').strip() or None,
                created_by=profile,
                member_count=0,
            )
            CommunityMember.objects.get_or_create(community=community, user=profile, defaults={'role': 'admin'})
            community.member_count = community.members.count()
            community.save(update_fields=['member_count'])
        except IntegrityError:
            return Response({'error': 'Could not create community.'}, status=409)
        except Exception as exc:
            return Response({'error': f'Failed to create: {exc}'}, status=500)

        return Response(_serialize_community(community, 'admin'), status=201)


# ── Community detail / update ─────────────────────────────────────────────────

class CommunityDetailView(views.APIView):
    def get_permissions(self):
        return [permissions.AllowAny()] if self.request.method == 'GET' else [permissions.IsAuthenticated()]

    def get(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        m = None
        join_request_status = None
        my_invite = None
        if request.user.is_authenticated:
            profile = _get_profile(request.user)
            m = CommunityMember.objects.filter(community=community, user=profile).first()
            if not m:
                jr = CommunityJoinRequest.objects.filter(community=community, user=profile).first()
                if jr: join_request_status = jr.status
                my_invite = CommunityInvite.objects.filter(
                    community=community, invited_user=profile,
                    status=CommunityInvite.STATUS_PENDING,
                ).first()

        return Response(_serialize_community(community, m, join_request_status, my_invite=my_invite))

    def patch(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        m = CommunityMember.objects.filter(community=community, user=profile).first()
        if community.created_by != profile and not (m and m.role == 'admin'):
            return Response({'error': 'Permission denied'}, status=403)

        for field in ('name', 'description', 'category', 'image_url', 'entry_question'):
            if field in request.data:
                v = request.data.get(field)
                if isinstance(v, str): v = v.strip()
                setattr(community, field, v or None if field in ('image_url', 'entry_question', 'description') else v)

        if 'is_private' in request.data:
            community.is_private = _coerce_bool(request.data['is_private'])
        if 'membership_type' in request.data:
            mt = request.data['membership_type']
            if mt in ('open', 'request', 'invite'):
                community.membership_type = mt
                community.is_private = mt != 'open'
        if 'rules' in request.data:
            community.rules = _normalise_rules(request.data['rules'])

        if not (community.name or '').strip():
            return Response({'error': 'Name is required'}, status=400)

        community.save()
        return Response(_serialize_community(community, m))


# ── Posts ─────────────────────────────────────────────────────────────────────

class CommunityPostsView(views.APIView):
    def get_permissions(self):
        return [permissions.AllowAny()] if self.request.method == 'GET' else [permissions.IsAuthenticated()]

    def get(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        sort       = (request.query_params.get('sort') or 'new').strip()
        media_only = request.query_params.get('media_only') == '1'

        qs = CommunityPost.objects.filter(community=community).select_related('author')
        if media_only:
            qs = qs.exclude(media_url__isnull=True).exclude(media_url='')

        if sort == 'popular':
            qs = qs.order_by('-is_pinned', '-likes_count', '-created_at')
        elif sort == 'trending':
            qs = qs.order_by('-is_pinned', '-comments_count', '-likes_count', '-created_at')
        else:
            qs = qs.order_by('-is_pinned', '-created_at')

        posts = list(qs[:50])

        liked_ids = set()
        if request.user.is_authenticated:
            profile = _get_profile(request.user)
            liked_ids = set(CommunityPostLike.objects.filter(
                user=profile, post__community=community
            ).values_list('post_id', flat=True))

        return Response([_serialize_post(p, liked_ids, include_comments=True) for p in posts])

    def post(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        profile = _get_profile(request.user)
        if not CommunityMember.objects.filter(community=community, user=profile).exists():
            return Response({'error': 'You must be a member to post'}, status=403)

        content    = (request.data.get('content') or '').strip()
        media_url  = request.data.get('media_url') or None
        media_type = (request.data.get('media_type') or '').strip().lower() or None

        if not content and not media_url:
            return Response({'error': 'Content or media is required'}, status=400)
        if media_type and media_type not in {'image', 'video'}:
            return Response({'error': 'media_type must be image or video'}, status=400)

        post = CommunityPost.objects.create(
            community=community, author=profile,
            content=content, media_url=media_url, media_type=media_type,
        )
        return Response(_serialize_post(post, set(), include_comments=False), status=201)


# ── Post likes ────────────────────────────────────────────────────────────────

class CommunityPostLikeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_post(self, community_id, post_id):
        try: return CommunityPost.objects.get(id=post_id, community_id=community_id)
        except CommunityPost.DoesNotExist: return None

    def post(self, request, community_id, post_id):
        post = self._get_post(community_id, post_id)
        if not post: return Response({'error': 'Not found'}, status=404)
        profile = _get_profile(request.user)
        _, created = CommunityPostLike.objects.get_or_create(post=post, user=profile)
        if created:
            post.likes_count = post.likes.count()
            post.save(update_fields=['likes_count'])
            notify_post_liked(post, profile)
        return Response({'liked': True, 'likes_count': post.likes_count})

    def delete(self, request, community_id, post_id):
        post = self._get_post(community_id, post_id)
        if not post: return Response({'error': 'Not found'}, status=404)
        profile = _get_profile(request.user)
        CommunityPostLike.objects.filter(post=post, user=profile).delete()
        post.likes_count = post.likes.count(); post.save(update_fields=['likes_count'])
        return Response({'liked': False, 'likes_count': post.likes_count})


# ── Post comments ─────────────────────────────────────────────────────────────

class CommunityPostCommentsView(views.APIView):
    def get_permissions(self):
        return [permissions.AllowAny()] if self.request.method == 'GET' else [permissions.IsAuthenticated()]

    def get(self, request, community_id, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id, community_id=community_id)
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        comments = post.comments.select_related('author').order_by('created_at')[:100]
        return Response([_serialize_comment(c) for c in comments])

    def post(self, request, community_id, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id, community_id=community_id)
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        content = (request.data.get('content') or '').strip()
        if not content:
            return Response({'error': 'Comment cannot be empty'}, status=400)
        if len(content) > 500:
            return Response({'error': 'Comment too long (max 500)'}, status=400)

        comment = CommunityPostComment.objects.create(post=post, author=profile, content=content)
        post.comments_count = post.comments.count()
        post.save(update_fields=['comments_count'])
        notify_post_commented(post, profile, content[:80])
        return Response(_serialize_comment(comment), status=201)

    def delete(self, request, community_id, post_id):
        comment_id = request.query_params.get('comment_id')
        if not comment_id:
            return Response({'error': 'comment_id required'}, status=400)
        try:
            post    = CommunityPost.objects.get(id=post_id, community_id=community_id)
            comment = CommunityPostComment.objects.get(id=comment_id, post=post)
        except (CommunityPost.DoesNotExist, CommunityPostComment.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        if str(comment.author_id) != str(profile.id) and not _is_mod_or_admin(profile, post.community):
            return Response({'error': 'Permission denied'}, status=403)

        comment.delete()
        post.comments_count = post.comments.count()
        post.save(update_fields=['comments_count'])
        return Response({'deleted': True})


# ── Post pin / unpin ──────────────────────────────────────────────────────────

class CommunityPostPinView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, community_id, post_id):
        try:
            community = Community.objects.get(id=community_id)
            post = CommunityPost.objects.get(id=post_id, community=community)
        except (Community.DoesNotExist, CommunityPost.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        if not _is_mod_or_admin(profile, community):
            return Response({'error': 'Permission denied'}, status=403)

        post.is_pinned = True
        post.save(update_fields=['is_pinned'])
        return Response({'is_pinned': True})

    def delete(self, request, community_id, post_id):
        try:
            community = Community.objects.get(id=community_id)
            post = CommunityPost.objects.get(id=post_id, community=community)
        except (Community.DoesNotExist, CommunityPost.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        if not _is_mod_or_admin(profile, community):
            return Response({'error': 'Permission denied'}, status=403)

        post.is_pinned = False
        post.save(update_fields=['is_pinned'])
        return Response({'is_pinned': False})


# ── Members ───────────────────────────────────────────────────────────────────

class CommunityMembersView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, community_id):
        try:
            Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        members = (CommunityMember.objects
                   .filter(community_id=community_id)
                   .select_related('user')
                   .order_by('joined_at')[:100])
        return Response([{
            'id':        str(m.id),
            'role':      m.role,
            'joined_at': m.joined_at.isoformat(),
            'user': {
                'id':           str(m.user.id),
                'username':     m.user.username,
                'display_name': m.user.display_name,
                'avatar_url':   m.user.avatar_url,
                'is_verified':  m.user.is_verified,
                'tier':         m.user.tier,
            },
        } for m in members])


# ── Join requests ─────────────────────────────────────────────────────────────

def _serialize_join_request(jr):
    return {
        'id':          str(jr.id),
        'status':      jr.status,
        'answer':      jr.answer,
        'created_at':  jr.created_at.isoformat(),
        'reviewed_at': jr.reviewed_at.isoformat() if jr.reviewed_at else None,
        'user': {
            'id':           str(jr.user.id),
            'username':     jr.user.username,
            'display_name': jr.user.display_name,
            'avatar_url':   jr.user.avatar_url,
            'is_verified':  jr.user.is_verified,
        },
    }


class CommunityJoinRequestsView(views.APIView):
    """Admin: list pending join requests.  User: cancel own request."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        if not _is_mod_or_admin(profile, community):
            return Response({'error': 'Permission denied'}, status=403)

        status_filter = request.query_params.get('status', 'pending')
        qs = (CommunityJoinRequest.objects
              .filter(community=community, status=status_filter)
              .select_related('user')
              .order_by('-created_at')[:100])
        return Response([_serialize_join_request(jr) for jr in qs])

    def delete(self, request, community_id):
        """User cancels their own pending request."""
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        deleted, _ = CommunityJoinRequest.objects.filter(
            community=community, user=profile, status=CommunityJoinRequest.STATUS_PENDING
        ).delete()
        if not deleted:
            return Response({'error': 'No pending request found'}, status=404)
        return Response({'cancelled': True})


class CommunityJoinRequestDetailView(views.APIView):
    """Admin: approve or reject a specific join request."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, community_id, request_id):
        try:
            community = Community.objects.get(id=community_id)
            jr = CommunityJoinRequest.objects.get(id=request_id, community=community)
        except (Community.DoesNotExist, CommunityJoinRequest.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        if not _is_mod_or_admin(profile, community):
            return Response({'error': 'Permission denied'}, status=403)

        action = (request.data.get('action') or '').strip()
        if action not in ('approve', 'reject'):
            return Response({'error': "action must be 'approve' or 'reject'"}, status=400)

        from django.utils import timezone
        jr.status = CommunityJoinRequest.STATUS_APPROVED if action == 'approve' else CommunityJoinRequest.STATUS_REJECTED
        jr.reviewed_by = profile
        jr.reviewed_at = timezone.now()
        jr.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

        if action == 'approve':
            CommunityMember.objects.get_or_create(community=community, user=jr.user)
            community.member_count = community.members.count()
            community.save(update_fields=['member_count'])

        notify_join_request_reviewed(jr)
        return Response(_serialize_join_request(jr))


# ── Invites ───────────────────────────────────────────────────────────────────

def _serialize_invite(invite):
    return {
        'id':           str(invite.id),
        'status':       invite.status,
        'created_at':   invite.created_at.isoformat(),
        'responded_at': invite.responded_at.isoformat() if invite.responded_at else None,
        'invited_user': {
            'id':           str(invite.invited_user.id),
            'username':     invite.invited_user.username,
            'display_name': invite.invited_user.display_name,
            'avatar_url':   invite.invited_user.avatar_url,
            'is_verified':  invite.invited_user.is_verified,
        },
        'invited_by': {
            'id':           str(invite.invited_by.id),
            'username':     invite.invited_by.username,
            'display_name': invite.invited_by.display_name,
        },
    }


class CommunityInvitesView(views.APIView):
    """Admin: send / list / cancel invites for a community."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        if not _is_mod_or_admin(profile, community):
            return Response({'error': 'Permission denied'}, status=403)

        status_filter = request.query_params.get('status', 'pending')
        invites = (CommunityInvite.objects
                   .filter(community=community, status=status_filter)
                   .select_related('invited_user', 'invited_by')
                   .order_by('-created_at')[:100])
        return Response([_serialize_invite(inv) for inv in invites])

    def post(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        if not _is_mod_or_admin(profile, community):
            return Response({'error': 'Permission denied'}, status=403)

        username = (request.data.get('username') or '').strip()
        user_id  = request.data.get('user_id') or None

        target = None
        if username:
            target = User.objects.filter(username=username).first()
        elif user_id:
            try:
                target = User.objects.filter(id=user_id).first()
            except Exception:
                pass

        if not target:
            return Response({'error': 'User not found'}, status=404)
        if str(target.id) == str(profile.id):
            return Response({'error': 'Cannot invite yourself'}, status=400)
        if CommunityMember.objects.filter(community=community, user=target).exists():
            return Response({'error': 'User is already a member'}, status=400)

        try:
            invite, created = CommunityInvite.objects.get_or_create(
                community=community,
                invited_user=target,
                defaults={'invited_by': profile, 'status': CommunityInvite.STATUS_PENDING},
            )
        except IntegrityError:
            invite = CommunityInvite.objects.get(community=community, invited_user=target)
            created = False

        if not created:
            if invite.status == CommunityInvite.STATUS_PENDING:
                return Response({'error': 'Invite already pending for this user'}, status=400)
            # Re-invite after declined / accepted
            invite.status = CommunityInvite.STATUS_PENDING
            invite.invited_by = profile
            invite.responded_at = None
            invite.save(update_fields=['status', 'invited_by', 'responded_at'])

        notify_invite_sent(invite)
        return Response(_serialize_invite(invite), status=201)

    def delete(self, request, community_id):
        """Cancel a pending invite.  Pass ?invite_id=<uuid>."""
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile = _get_profile(request.user)
        if not _is_mod_or_admin(profile, community):
            return Response({'error': 'Permission denied'}, status=403)

        invite_id = request.query_params.get('invite_id')
        if not invite_id:
            return Response({'error': 'invite_id required'}, status=400)
        try:
            invite = CommunityInvite.objects.get(
                id=invite_id, community=community,
                status=CommunityInvite.STATUS_PENDING,
            )
        except CommunityInvite.DoesNotExist:
            return Response({'error': 'Pending invite not found'}, status=404)

        invite.delete()
        return Response({'cancelled': True})


class CommunityInviteRespondView(views.APIView):
    """Invited user accepts or declines a specific invite."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, community_id, invite_id):
        from django.utils import timezone as tz
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)
        try:
            invite = CommunityInvite.objects.select_related(
                'invited_user', 'invited_by', 'community'
            ).get(id=invite_id, community=community, status=CommunityInvite.STATUS_PENDING)
        except CommunityInvite.DoesNotExist:
            return Response({'error': 'Invite not found or no longer pending'}, status=404)

        profile = _get_profile(request.user)
        if str(invite.invited_user_id) != str(profile.id):
            return Response({'error': 'This invite is not for you'}, status=403)

        action = (request.data.get('action') or '').strip()
        if action not in ('accept', 'decline'):
            return Response({'error': "action must be 'accept' or 'decline'"}, status=400)

        if action == 'accept':
            invite.status = CommunityInvite.STATUS_ACCEPTED
            invite.responded_at = tz.now()
            invite.save(update_fields=['status', 'responded_at'])
            CommunityMember.objects.get_or_create(community=community, user=profile)
            community.member_count = community.members.count()
            community.save(update_fields=['member_count'])
        else:
            invite.status = CommunityInvite.STATUS_DECLINED
            invite.responded_at = tz.now()
            invite.save(update_fields=['status', 'responded_at'])

        notify_invite_responded(invite)
        return Response({
            'status':       invite.status,
            'community_id': str(community.id),
            'is_member':    action == 'accept',
            'member_count': community.member_count,
        })
