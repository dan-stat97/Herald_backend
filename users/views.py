from rest_framework import viewsets, mixins
from rest_framework.decorators import action
class UserProfileViewSet(viewsets.ModelViewSet):
	queryset = UserProfile.objects.all()
	serializer_class = UserProfileSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		# Allow filtering by username or id
		queryset = super().get_queryset()
		username = self.request.query_params.get('username')
		if username:
			queryset = queryset.filter(username=username)
		return queryset

	@action(detail=False, methods=['get', 'patch', 'delete'], url_path='me')
	def me(self, request):
		profile = UserProfile.objects.get(user_id=request.user)
		if request.method == 'GET':
			return Response(UserProfileSerializer(profile).data)
		elif request.method == 'PATCH':
			serializer = UserProfileSerializer(profile, data=request.data, partial=True)
			serializer.is_valid(raise_exception=True)
			serializer.save()
			return Response(serializer.data)
		elif request.method == 'DELETE':
			profile.delete()
			request.user.delete()
			return Response({'success': True})

	@action(detail=False, methods=['get'], url_path='me/stats')
	def stats(self, request):
		profile = UserProfile.objects.get(user_id=request.user)
		# Example stats, expand as needed
		stats = {
			'posts_count': profile.posts.count() if hasattr(profile, 'posts') else 0,
			'followers_count': profile.followers.count() if hasattr(profile, 'followers') else 0,
			'following_count': profile.following.count() if hasattr(profile, 'following') else 0,
			'reputation': profile.reputation,
		}
		return Response(stats)

	@action(detail=False, methods=['patch'], url_path='me/settings')
	def update_settings(self, request):
		profile = UserProfile.objects.get(user_id=request.user)
		# Assume settings fields are in request.data
		allowed_fields = ['notifications_enabled', 'privacy_level', 'email_updates']
		for field in allowed_fields:
			if field in request.data:
				setattr(profile, field, request.data[field])
		profile.save()
		return Response({'success': True, 'settings': {f: getattr(profile, f, None) for f in allowed_fields}})

from rest_framework import status, permissions, generics, views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import User as UserProfile
from .serializers import UserSignupSerializer, UserProfileSerializer

class SignupView(generics.CreateAPIView):
	serializer_class = UserSignupSerializer
	permission_classes = [permissions.AllowAny]

	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		if User.objects.filter(username=data['username']).exists() or User.objects.filter(email=data['email']).exists():
			return Response({'error': 'User already exists'}, status=409)
		user = User.objects.create_user(
			username=data['username'],
			email=data['email'],
			password=data['password'],
			first_name=data.get('full_name', '')
		)
		profile = UserProfile.objects.create(
			user_id=user,
			username=data['username'],
			display_name=data['display_name'],
			full_name=data.get('full_name', ''),
			email=data['email']
		)
		# Optionally create wallet here
		refresh = RefreshToken.for_user(user)
		return Response({
			'user': UserProfileSerializer(profile).data,
			'session': {
				'access_token': str(refresh.access_token),
				'token_type': 'Bearer',
				'expires_in': 3600
			}
		}, status=201)

class SigninView(views.APIView):
	permission_classes = [permissions.AllowAny]
	def post(self, request):
		email = request.data.get('email')
		password = request.data.get('password')
		try:
			user = User.objects.get(email=email)
		except User.DoesNotExist:
			return Response({'error': 'User not found'}, status=404)
		user = authenticate(username=user.username, password=password)
		if not user:
			return Response({'error': 'Invalid credentials'}, status=401)
		refresh = RefreshToken.for_user(user)
		profile = UserProfile.objects.get(user_id=user)
		return Response({
			'user': UserProfileSerializer(profile).data,
			'session': {
				'access_token': str(refresh.access_token),
				'token_type': 'Bearer',
				'expires_in': 3600
			}
		})

class SignoutView(views.APIView):
	permission_classes = [permissions.IsAuthenticated]
	def post(self, request):
		logout(request)
		return Response({'success': True})

class RefreshView(TokenRefreshView):
	permission_classes = [permissions.AllowAny]

class CurrentUserView(views.APIView):
	permission_classes = [permissions.IsAuthenticated]
	def get(self, request):
		profile = UserProfile.objects.get(user_id=request.user)
		return Response(UserProfileSerializer(profile).data)
