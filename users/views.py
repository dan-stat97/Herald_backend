import json
import os
import re
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import parse_qs

from django.contrib.auth import authenticate, logout
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from rest_framework import generics, permissions, status, viewsets, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User as UserProfile
from .serializers import UserProfileSerializer, UserReplySerializer, UserSignupSerializer
from posts.models import Comment, Post

AuthUser = get_user_model()
KINGSCHAT_TOKEN_URL = 'https://connect.kingsch.at/developer/oauth2/token'
KINGSCHAT_PROFILE_URL = 'https://connect.kingsch.at/developer/api/profile'
KINGSCHAT_USERNAME_RE = re.compile(r'[^a-z0-9_]+')


class KingsChatAuthError(Exception):
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.status_code = status_code


def ensure_user_profile(auth_user):
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


def create_wallet_if_missing(profile):
    from wallets.models import Wallet
    Wallet.objects.get_or_create(user_id=profile, defaults={'httn_points': 100})


def kingschat_request(url, method='GET', payload=None, headers=None):
    request_headers = {'Accept': 'application/json'}
    if headers:
        request_headers.update(headers)

    body = None
    if payload is not None:
        body = json.dumps(payload).encode('utf-8')
        request_headers.setdefault('Content-Type', 'application/json')

    req = urllib_request.Request(url, data=body, headers=request_headers, method=method)

    try:
        with urllib_request.urlopen(req, timeout=20) as response:
            raw = response.read().decode('utf-8')
            return json.loads(raw) if raw else {}
    except urllib_error.HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='ignore')
        payload = {}
        if raw:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {'detail': raw}
        raise KingsChatAuthError(
            payload.get('user_message') or payload.get('detail') or payload.get('code') or 'KingsChat request failed',
            status_code=exc.code,
        )
    except urllib_error.URLError as exc:
        raise KingsChatAuthError(f'KingsChat is unreachable: {exc.reason}', status_code=status.HTTP_502_BAD_GATEWAY)


def parse_kingschat_name(name):
    cleaned = (name or '').strip()
    if not cleaned:
        return 'KingsChat', ''
    parts = cleaned.split(' ', 1)
    return parts[0], parts[1] if len(parts) > 1 else ''


def build_unique_username(seed):
    base = KINGSCHAT_USERNAME_RE.sub('', (seed or '').lower())
    base = base[:24] if base else 'kingschatuser'
    if len(base) < 3:
        base = f'{base}user'

    candidate = base
    suffix = 1
    while AuthUser.objects.filter(username=candidate).exists():
        candidate = f'{base[:20]}{suffix}'
        suffix += 1
    return candidate


def find_or_create_kingschat_user(profile_payload):
    kingschat_id = str(profile_payload.get('id') or '').strip()
    email = (profile_payload.get('email') or '').strip().lower()
    username_seed = profile_payload.get('username') or profile_payload.get('name') or email.split('@')[0] or 'kingschatuser'

    profile = None
    auth_user = None

    if kingschat_id:
        profile = UserProfile.objects.filter(kingschat_id=kingschat_id).select_related('user_id').first()
        if profile:
            auth_user = profile.user_id

    if auth_user is None and email:
        auth_user = AuthUser.objects.filter(email__iexact=email).first()

    if auth_user is None:
        first_name, last_name = parse_kingschat_name(profile_payload.get('name'))
        auth_user = AuthUser.objects.create(
            username=build_unique_username(username_seed),
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        auth_user.set_unusable_password()
        auth_user.save(update_fields=['password'])

    profile = ensure_user_profile(auth_user)
    updates = []

    mapped_username = build_unique_username(username_seed) if profile.username != auth_user.username and AuthUser.objects.filter(username=profile.username).exclude(pk=auth_user.pk).exists() else (profile_payload.get('username') or auth_user.username)
    if mapped_username and profile.username != mapped_username:
        profile.username = mapped_username[:100]
        updates.append('username')
        if auth_user.username != profile.username and not AuthUser.objects.filter(username=profile.username).exclude(pk=auth_user.pk).exists():
            auth_user.username = profile.username
            auth_user.save(update_fields=['username'])

    full_name = (profile_payload.get('name') or profile.full_name or auth_user.get_full_name() or profile.username).strip()
    display_name = (profile_payload.get('name') or profile.display_name or profile.username).strip()
    avatar_url = profile_payload.get('avatar') or profile.avatar_url
    kingschat_username = profile_payload.get('username') or profile.kingschat_username

    if display_name and profile.display_name != display_name:
        profile.display_name = display_name[:200]
        updates.append('display_name')
    if full_name and profile.full_name != full_name:
        profile.full_name = full_name[:200]
        updates.append('full_name')
    if email and profile.email != email:
        profile.email = email
        updates.append('email')
        if auth_user.email != email:
            auth_user.email = email
            auth_user.save(update_fields=['email'])
    if avatar_url and profile.avatar_url != avatar_url:
        profile.avatar_url = avatar_url
        updates.append('avatar_url')
    if kingschat_id and profile.kingschat_id != kingschat_id:
        profile.kingschat_id = kingschat_id
        updates.append('kingschat_id')
    if kingschat_username and profile.kingschat_username != kingschat_username:
        profile.kingschat_username = kingschat_username[:255]
        updates.append('kingschat_username')
    if profile.auth_provider != 'kingschat':
        profile.auth_provider = 'kingschat'
        updates.append('auth_provider')

    if updates:
        profile.save(update_fields=list(dict.fromkeys(updates + ['updated_at'])))

    create_wallet_if_missing(profile)
    return auth_user, profile


def fetch_kingschat_profile(code=None, access_token=None):
    token = access_token
    if code:
        client_id = os.getenv('KINGSCHAT_CLIENT_ID', '34cbe6fd-45ba-43d7-9cea-62cf1e439e40').strip()
        if not client_id:
            raise KingsChatAuthError('KingsChat client id is not configured on the backend.', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        token_payload = kingschat_request(
            KINGSCHAT_TOKEN_URL,
            method='POST',
            payload={
                'grant_type': 'code',
                'client_id': client_id,
                'code': code,
            },
        )
        token = token_payload.get('access_token')

    if not token:
        raise KingsChatAuthError('KingsChat authorization code or access token is required.')

    profile_payload = kingschat_request(
        KINGSCHAT_PROFILE_URL,
        headers={'authorization': f'Bearer {token}'},
    )
    return profile_payload.get('profile') or profile_payload


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        username = self.request.query_params.get('username')
        if username:
            queryset = queryset.filter(username=username)

        sort = self.request.query_params.get('sort')
        allowed_sort_fields = {'created_at', 'updated_at', 'reputation', 'username', 'display_name'}
        if sort:
            sort_field = sort.lstrip('-')
            if sort_field in allowed_sort_fields:
                queryset = queryset.order_by(sort)

        limit = self.request.query_params.get('limit')
        if limit:
            try:
                limit_value = int(limit)
                if limit_value > 0:
                    queryset = queryset[:limit_value]
            except (TypeError, ValueError):
                pass
        return queryset

    @action(detail=False, methods=['get', 'patch', 'delete'], url_path='me')
    def me(self, request):
        profile = ensure_user_profile(request.user)
        if request.method == 'GET':
            return Response(UserProfileSerializer(profile).data)
        if request.method == 'PATCH':
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        profile.delete()
        request.user.delete()
        return Response({'success': True})

    @action(detail=False, methods=['get'], url_path='me/stats')
    def stats(self, request):
        profile = ensure_user_profile(request.user)
        stats = {
            'posts_count': profile.posts.count() if hasattr(profile, 'posts') else 0,
            'followers_count': profile.followers.count() if hasattr(profile, 'followers') else 0,
            'following_count': profile.following.count() if hasattr(profile, 'following') else 0,
            'reputation': profile.reputation,
        }
        return Response(stats)

    @action(detail=False, methods=['patch'], url_path='me/settings')
    def update_settings(self, request):
        profile = ensure_user_profile(request.user)
        allowed_fields = ['notifications_enabled', 'privacy_level', 'email_updates']
        for field in allowed_fields:
            if field in request.data:
                setattr(profile, field, request.data[field])
        profile.save()
        return Response({'success': True, 'settings': {f: getattr(profile, f, None) for f in allowed_fields}})


class SignupView(generics.CreateAPIView):
    serializer_class = UserSignupSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        full_name = data['full_name'].strip()
        parts = full_name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''
        display_name = data.get('display_name') or data['username']
        if AuthUser.objects.filter(username=data['username']).exists() or AuthUser.objects.filter(email=data['email']).exists():
            return Response({'error': 'User already exists'}, status=409)
        user = AuthUser.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=first_name,
            last_name=last_name,
        )
        profile = UserProfile.objects.create(
            user_id=user,
            username=data['username'],
            display_name=display_name,
            full_name=full_name,
            email=data['email'],
            auth_provider='password',
        )
        create_wallet_if_missing(profile)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(profile).data,
            'session': {
                'access_token': str(refresh.access_token),
                'token_type': 'Bearer',
                'expires_in': 3600,
            },
            'refresh': str(refresh),
        }, status=201)


class SigninView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = AuthUser.objects.get(email=email)
        except AuthUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        user = authenticate(username=user.username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=401)
        refresh = RefreshToken.for_user(user)
        profile = ensure_user_profile(user)
        return Response({
            'user': UserProfileSerializer(profile).data,
            'session': {
                'access_token': str(refresh.access_token),
                'token_type': 'Bearer',
                'expires_in': 3600,
            },
            'refresh': str(refresh),
        })


class KingsChatAuthView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get('code')
        access_token = request.data.get('access_token') or request.data.get('accessToken')

        try:
            kingschat_profile = fetch_kingschat_profile(code=code, access_token=access_token)
            user, profile = find_or_create_kingschat_user(kingschat_profile)
        except KingsChatAuthError as exc:
            return Response({'error': str(exc)}, status=exc.status_code)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(profile).data,
            'session': {
                'access_token': str(refresh.access_token),
                'token_type': 'Bearer',
                'expires_in': 3600,
            },
            'refresh': str(refresh),
            'provider': 'kingschat',
        })



class KingsChatCallbackView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def _collect_incoming(self, request):
        sources = [request.GET]
        if request.method != 'GET':
            try:
                if request.data:
                    sources.append(request.data)
            except Exception:
                pass
            if request.POST:
                sources.append(request.POST)
            raw_body = request.body.decode('utf-8', errors='ignore') if request.body else ''
            if raw_body:
                try:
                    parsed_json = json.loads(raw_body)
                    if isinstance(parsed_json, dict):
                        sources.append(parsed_json)
                except json.JSONDecodeError:
                    pass
                parsed_form = {
                    key: values[-1] if isinstance(values, list) and values else values
                    for key, values in parse_qs(raw_body, keep_blank_values=True).items()
                }
                if parsed_form:
                    sources.append(parsed_form)
        return sources

    def _render_bridge(self, request):
        sources = self._collect_incoming(request)

        def read(key):
            for source in sources:
                try:
                    value = source.get(key)
                except Exception:
                    value = None
                if value:
                    return value
            return None

        app_redirect_uri = read('app_redirect_uri') or 'heraldsocial://auth/kingschat'
        payload = {}
        aliases = {
            'code': ('code',),
            'access_token': ('access_token', 'accessToken'),
            'refresh_token': ('refresh_token', 'refreshToken'),
            'expires_in_millis': ('expires_in_millis', 'expiresInMillis'),
            'error': ('error',),
            'error_description': ('error_description', 'errorDescription'),
            'state': ('state',),
        }
        for target_key, keys in aliases.items():
            for key in keys:
                value = read(key)
                if value:
                    payload[target_key] = value
                    break
        html = f"""
<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Finishing KingsChat sign in</title>
    <style>
      body {{ background:#0a0a0a; color:#f0f0f0; font-family:Arial,sans-serif; display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; }}
      .card {{ max-width:420px; padding:24px; border:1px solid #1f1f1f; border-radius:20px; background:#111111; text-align:center; }}
      h1 {{ font-size:22px; margin:0 0 12px; }}
      p {{ color:#9ca3af; line-height:1.5; }}
      a {{ display:inline-block; margin-top:16px; color:#d4a847; text-decoration:none; font-weight:700; }}
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1>Finishing KingsChat sign in</h1>
      <p>If Herald does not reopen automatically, tap the button below.</p>
      <a id=\"continueLink\" href=\"#\">Open Herald Social</a>
    </div>
    <script>
      (function () {{
        var appRedirectUri = {json.dumps(app_redirect_uri)};
        var target = new URL(appRedirectUri);
        var payload = {json.dumps(payload)};
        Object.keys(payload).forEach(function(key) {{
          target.searchParams.set(key, payload[key]);
        }});
        var searchParams = new URLSearchParams(window.location.search);
        var hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ''));
        hashParams.forEach(function(value, key) {{
          if (!searchParams.has(key)) searchParams.set(key, value);
        }});
        searchParams.delete('app_redirect_uri');
        searchParams.forEach(function(value, key) {{
          if (!target.searchParams.has(key)) {{
            target.searchParams.set(key, value);
          }}
        }});
        var href = target.toString();
        document.getElementById('continueLink').setAttribute('href', href);
        window.location.replace(href);
      }})();
    </script>
  </body>
</html>
"""
        return HttpResponse(html)

    def get(self, request):
        return self._render_bridge(request)

    def post(self, request):
        return self._render_bridge(request)

class SignoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'success': True})


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class SessionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = ensure_user_profile(request.user)
        return Response({
            'authenticated': True,
            'user': UserProfileSerializer(profile).data,
        })


class ChangePasswordView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not current_password or not new_password:
            return Response({'error': 'current_password and new_password are required'}, status=400)
        if not request.user.check_password(current_password):
            return Response({'error': 'Current password is incorrect'}, status=400)
        request.user.set_password(new_password)
        request.user.save()
        return Response({'success': True})


class UserByUsernameView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, username):
        try:
            profile = UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        return Response(UserProfileSerializer(profile).data)


class UserPostsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk=None):
        if pk is None:
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=401)
            try:
                profile = UserProfile.objects.get(user_id=request.user)
            except UserProfile.DoesNotExist:
                return Response({'error': 'User profile not found'}, status=404)
        else:
            try:
                profile = UserProfile.objects.get(pk=pk)
            except UserProfile.DoesNotExist:
                return Response({'error': 'User not found'}, status=404)

        tab = request.query_params.get('tab', 'posts')
        base_posts = Post.objects.select_related('author_id', 'author_id__user_id')

        if tab == 'likes':
            posts = base_posts.filter(likes__user=profile).order_by('-likes__created_at').distinct()
        elif tab == 'media':
            posts = (
                base_posts.filter(author_id=profile)
                .exclude(media_url__isnull=True)
                .exclude(media_url='')
                .order_by('-created_at')
            )
        else:
            posts = base_posts.filter(author_id=profile).order_by('-created_at')

        from posts.serializers import PostSerializer

        try:
            serializer = PostSerializer(posts, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as exc:
            print(f'Error serializing posts: {exc}')
            return Response([])


class UserRepliesView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk=None):
        if pk is None:
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=401)
            try:
                profile = UserProfile.objects.get(user_id=request.user)
            except UserProfile.DoesNotExist:
                return Response({'error': 'User profile not found'}, status=404)
        else:
            try:
                profile = UserProfile.objects.get(pk=pk)
            except UserProfile.DoesNotExist:
                return Response({'error': 'User not found'}, status=404)

        replies = (
            Comment.objects
            .filter(author=profile)
            .select_related('post', 'post__author_id', 'post__author_id__user_id')
            .order_by('-created_at')
        )

        try:
            serializer = UserReplySerializer(replies, many=True)
            return Response(serializer.data)
        except Exception as exc:
            print(f'Error serializing replies: {exc}')
            return Response([])


class UserTasksView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        return Response([])


class ClaimTaskRewardView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, task_id):
        return Response({'success': True, 'reward': 0})


class CurrentUserView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = ensure_user_profile(request.user)
        return Response(UserProfileSerializer(profile).data)




