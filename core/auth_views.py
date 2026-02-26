# core/auth_views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone  # <-- ADD THIS LINE
from core.models import Profiles, Wallets, Posts, Follow
from django.utils import timezone  # Add this line
import uuid

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """Create new user account"""
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        username = request.data.get('username')
        full_name = request.data.get('full_name', '')
        
        # Validation
        if not email or not password or not username:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Missing required fields',
                    'details': {
                        'required': ['email', 'password', 'username']
                    }
                }
            }, status=400)
        
        # Check if user exists
        if User.objects.filter(username=username).exists():
            return Response({
                'error': {
                    'code': 'CONFLICT',
                    'message': 'Username already exists'
                }
            }, status=409)
        
        if User.objects.filter(email=email).exists():
            return Response({
                'error': {
                    'code': 'CONFLICT',
                    'message': 'Email already exists'
                }
            }, status=409)
        
        # Create auth user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name
        )
        
        # Create profile
        profile = Profiles.objects.create(
            id=uuid.uuid4(),
            user_id=user.id,
            username=username,
            full_name=full_name,
            display_name=username,
            verified=False,
            pro_status=False,
            balance=0
        )
        
        # Create wallet with welcome bonus
        wallet = Wallets.objects.create(
            id=uuid.uuid4(),
            user_id=profile.id,  # Use profile.id (UUID), not user.id (integer)
            httn_points=100,
            httn_tokens=0,
            espees=0,
            pending_rewards=0,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        
        # Generate token
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': profile.id,
                'email': user.email,
                'user_id': user.id,
                'username': profile.username,
                'display_name': profile.display_name,
                'full_name': profile.full_name
            },
            'session': {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'token_type': 'Bearer',
                'expires_in': 3600
            }
        }, status=201)
        
    except Exception as e:
        return Response({
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def signout(request):
    """Logout user (blacklist token)"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'success': True})
    except:
        return Response({'success': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current authenticated user with profile and wallet"""
    try:
        profile = Profiles.objects.get(user_id=request.user.id)
        
        # Get wallet - use profile.id (UUID)
        wallet = Wallets.objects.filter(user_id=profile.id).first()
        
        # Get stats
        posts_count = Posts.objects.filter(author_id=request.user.id).count()
        followers_count = Follow.objects.filter(following_id=profile.id).count()
        following_count = Follow.objects.filter(follower_id=profile.id).count()
        
        response_data = {
            'id': profile.id,
            'user_id': request.user.id,
            'username': profile.username,
            'display_name': profile.display_name,
            'full_name': profile.full_name,
            'email': request.user.email,
            'avatar_url': profile.avatar_url,
            'bio': getattr(profile, 'bio', ''),
            'tier': 'creator' if profile.pro_status else 'free',
            'reputation': profile.balance or 0,
            'is_verified': profile.verified,
            'is_creator': profile.pro_status,
            'stats': {
                'posts_count': posts_count,
                'followers_count': followers_count,
                'following_count': following_count
            },
            'created_at': profile.created_at.isoformat()
        }
        
        # Add wallet if it exists
        if wallet:
            response_data['wallet'] = {
                'httn_points': wallet.httn_points,
                'httn_tokens': str(wallet.httn_tokens),
                'espees': str(wallet.espees),
                'pending_rewards': wallet.pending_rewards
            }
        else:
            response_data['wallet'] = None
        
        return Response(response_data)
        
    except Profiles.DoesNotExist:
        return Response({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Profile not found'
            }
        }, status=404)