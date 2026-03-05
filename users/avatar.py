from rest_framework import views, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import User as UserProfile
from .serializers import UserProfileSerializer


class AvatarUploadView(views.APIView):
    """Upload avatar/profile picture"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Upload avatar image"""
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=404)
        
        if 'avatar' not in request.FILES:
            return Response(
                {'error': 'Avatar file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        avatar_file = request.FILES['avatar']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if avatar_file.content_type not in allowed_types:
            return Response(
                {'error': f'Invalid file type. Allowed: {", ".join(allowed_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024
        if avatar_file.size > max_size:
            return Response(
                {'error': f'File too large. Max size: 5MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Save avatar
            profile.avatar_url = f'/media/avatars/{request.user.id}/{avatar_file.name}'
            profile.save()
            
            return Response({
                'success': True,
                'message': 'Avatar uploaded successfully',
                'avatar_url': profile.avatar_url,
                'user': UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to upload avatar: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
