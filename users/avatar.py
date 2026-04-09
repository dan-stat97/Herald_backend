from rest_framework import permissions, status, views
from rest_framework.response import Response

from .models import User as UserProfile
from .serializers import UserProfileSerializer


ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def _get_profile(request):
    try:
        return UserProfile.objects.get(user_id=request.user)
    except UserProfile.DoesNotExist:
        return None


def _validate_image_upload(uploaded_file, field_label):
    if uploaded_file.content_type not in ALLOWED_IMAGE_TYPES:
        return Response(
            {'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_IMAGE_TYPES)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if uploaded_file.size > MAX_IMAGE_SIZE:
        return Response(
            {'error': f'File too large. Max size: {MAX_IMAGE_SIZE // (1024 * 1024)}MB'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None


def _serialize_profile(profile, message, field_name):
    return Response(
        {
            'success': True,
            'message': message,
            field_name: getattr(profile, field_name),
            'user': UserProfileSerializer(profile).data,
        },
        status=status.HTTP_200_OK,
    )


class AvatarUploadView(views.APIView):
    """Upload avatar/profile picture"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Upload avatar image"""
        profile = _get_profile(request)
        if not profile:
            return Response({'error': 'User profile not found'}, status=404)

        if 'avatar' not in request.FILES:
            return Response(
                {'error': 'Avatar file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        avatar_file = request.FILES['avatar']
        validation_error = _validate_image_upload(avatar_file, 'Avatar')
        if validation_error:
            return validation_error
        
        try:
            from django.conf import settings as django_settings
            import cloudinary.uploader

            if django_settings.CLOUDINARY_ENABLED:
                # Upload to Cloudinary with face-cropping to a 400×400 thumbnail
                result = cloudinary.uploader.upload(
                    avatar_file,
                    folder='heraldsocial/profiles/avatars',
                    public_id=f'user_{request.user.id}',
                    overwrite=True,
                    resource_type='image',
                    quality='auto',
                    fetch_format='auto',
                    width=400,
                    height=400,
                    crop='fill',
                    gravity='face',
                )
                avatar_url = result['secure_url']
            else:
                # Dev fallback — local path (ephemeral on Render, fine for local dev)
                avatar_url = f'/media/avatars/{request.user.id}/{avatar_file.name}'

            profile.avatar_url = avatar_url
            profile.save()
            return _serialize_profile(profile, 'Avatar uploaded successfully', 'avatar_url')

        except Exception as e:
            return Response(
                {'error': f'Failed to upload avatar: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CoverUploadView(views.APIView):
    """Upload profile banner / header image"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = _get_profile(request)
        if not profile:
            return Response({'error': 'User profile not found'}, status=404)

        if 'cover' not in request.FILES:
            return Response({'error': 'Cover file is required'}, status=status.HTTP_400_BAD_REQUEST)

        cover_file = request.FILES['cover']
        validation_error = _validate_image_upload(cover_file, 'Cover')
        if validation_error:
            return validation_error

        try:
            from django.conf import settings as django_settings
            import cloudinary.uploader

            if django_settings.CLOUDINARY_ENABLED:
                result = cloudinary.uploader.upload(
                    cover_file,
                    folder='heraldsocial/profiles/covers',
                    public_id=f'user_{request.user.id}_cover',
                    overwrite=True,
                    resource_type='image',
                    quality='auto',
                    fetch_format='auto',
                    width=1500,
                    height=500,
                    crop='fill',
                    gravity='auto',
                )
                cover_url = result['secure_url']
            else:
                cover_url = f'/media/covers/{request.user.id}/{cover_file.name}'

            profile.cover_url = cover_url
            profile.save()
            return _serialize_profile(profile, 'Cover uploaded successfully', 'cover_url')
        except Exception as e:
            return Response(
                {'error': f'Failed to upload cover: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
