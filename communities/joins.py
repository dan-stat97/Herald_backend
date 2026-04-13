from django.utils import timezone
from rest_framework import permissions, status, views
from rest_framework.response import Response

from .models import Community, CommunityMember, CommunityJoinRequest
from users.models import User as UserProfile


def _get_profile(auth_user):
    profile, created = UserProfile.objects.get_or_create(
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


class CommunityJoinView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        user_profile = _get_profile(request.user)

        # Already a member?
        if CommunityMember.objects.filter(community=community, user=user_profile).exists():
            return Response({'error': 'Already a member of this community'}, status=400)

        mt = community.membership_type

        # Invite-only: no self-join
        if mt == Community.MEMBERSHIP_INVITE:
            return Response({'error': 'This community is invite only'}, status=403)

        # Request-to-join: create or surface existing join request
        if mt == Community.MEMBERSHIP_REQUEST:
            jr, created = CommunityJoinRequest.objects.get_or_create(
                community=community,
                user=user_profile,
                defaults={'answer': (request.data.get('answer') or '').strip() or None},
            )
            if not created and jr.status == CommunityJoinRequest.STATUS_REJECTED:
                # Allow re-application after rejection
                jr.status = CommunityJoinRequest.STATUS_PENDING
                jr.answer = (request.data.get('answer') or '').strip() or None
                jr.reviewed_at = None
                jr.reviewed_by = None
                jr.save(update_fields=['status', 'answer', 'reviewed_at', 'reviewed_by'])
                created = True
            return Response({
                'join_request': True,
                'status': jr.status,
                'message': 'Join request submitted' if created else f'Request already {jr.status}',
                'community_id': str(community.id),
            }, status=201 if created else 200)

        # Open: direct join
        CommunityMember.objects.get_or_create(community=community, user=user_profile)
        community.member_count = community.members.count()
        community.save(update_fields=['member_count'])

        return Response({
            'success': True,
            'message': f'Joined {community.name}',
            'community_id': str(community.id),
            'community_name': community.name,
            'member_count': community.member_count,
        }, status=200)

    def delete(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        user_profile = _get_profile(request.user)

        # Also cancel any pending join request
        CommunityJoinRequest.objects.filter(
            community=community, user=user_profile, status=CommunityJoinRequest.STATUS_PENDING
        ).delete()

        try:
            member = CommunityMember.objects.get(community=community, user=user_profile)
            member.delete()
        except CommunityMember.DoesNotExist:
            return Response({'error': 'Not a member of this community'}, status=400)

        community.member_count = community.members.count()
        community.save(update_fields=['member_count'])

        return Response({
            'success': True,
            'message': f'Left {community.name}',
            'community_id': str(community.id),
            'community_name': community.name,
            'member_count': community.member_count,
        }, status=200)
