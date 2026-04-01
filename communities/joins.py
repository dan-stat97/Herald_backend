from rest_framework import permissions, status, views
from rest_framework.response import Response

from .models import Community, CommunityMember
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

        member, created = CommunityMember.objects.get_or_create(
            community=community,
            user=user_profile,
        )
        if not created:
            return Response({'error': 'Already a member of this community'}, status=status.HTTP_400_BAD_REQUEST)

        community.member_count = community.members.count()
        community.save(update_fields=['member_count'])

        return Response({
            'success': True,
            'message': f'Joined {community.name}',
            'community_id': str(community.id),
            'community_name': community.name,
            'member_count': community.member_count
        }, status=status.HTTP_200_OK)

    def delete(self, request, community_id):
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)

        user_profile = _get_profile(request.user)

        try:
            member = CommunityMember.objects.get(community=community, user=user_profile)
            member.delete()
        except CommunityMember.DoesNotExist:
            return Response({'error': 'Not a member of this community'}, status=status.HTTP_400_BAD_REQUEST)

        community.member_count = community.members.count()
        community.save(update_fields=['member_count'])

        return Response({
            'success': True,
            'message': f'Left {community.name}',
            'community_id': str(community.id),
            'community_name': community.name,
            'member_count': community.member_count
        }, status=status.HTTP_200_OK)
