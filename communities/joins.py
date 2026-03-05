from rest_framework import views, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import Community, CommunityMember
from users.models import User as UserProfile


class CommunityJoinView(views.APIView):
    """Join or leave a community"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, community_id):
        """Join a community"""
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)
        
        try:
            user_profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=404)
        
        # Check if already a member
        try:
            member = CommunityMember.objects.get(community=community, user=user_profile)
            return Response(
                {'error': 'Already a member of this community'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except CommunityMember.DoesNotExist:
            pass
        
        try:
            # Create membership
            CommunityMember.objects.create(
                community=community,
                user=user_profile
            )
            
            # Update member count
            community.member_count = community.members.count()
            community.save()
            
            return Response({
                'success': True,
                'message': f'Joined {community.name}',
                'community_id': str(community.id),
                'community_name': community.name,
                'member_count': community.member_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to join community: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, community_id):
        """Leave a community"""
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=404)
        
        try:
            user_profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=404)
        
        try:
            member = CommunityMember.objects.get(community=community, user=user_profile)
            member.delete()
            
            # Update member count
            community.member_count = community.members.count()
            community.save()
            
            return Response({
                'success': True,
                'message': f'Left {community.name}',
                'community_id': str(community.id),
                'community_name': community.name,
                'member_count': community.member_count
            }, status=status.HTTP_200_OK)
            
        except CommunityMember.DoesNotExist:
            return Response(
                {'error': 'Not a member of this community'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to leave community: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

