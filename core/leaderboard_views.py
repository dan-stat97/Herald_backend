from django.core.cache import cache
from django.db.models import Count
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import User as UserProfile
from users.serializers import UserProfileSerializer
from wallets.models import Wallet
from .leaderboard_cache import get_leaderboard_cache_version


class LeaderboardViewSet(viewsets.GenericViewSet):
    """Leaderboard endpoints with short public caching."""

    permission_classes = [permissions.AllowAny]

    def _serialize_profile(self, profile, rank, extra=None):
        data = UserProfileSerializer(profile).data
        data['rank'] = rank
        data['user_id'] = str(profile.id)
        data['display_name'] = profile.display_name or profile.username or 'Unknown'
        data['is_verified'] = profile.is_verified
        data['avatar_url'] = profile.avatar_url
        data['tier'] = profile.tier or 'participant'
        data['reputation'] = profile.reputation or 0
        data['total_engagement'] = 0
        if extra:
            data.update(extra)
        return data

    def _cache_response(self, metric, limit, builder):
        version = get_leaderboard_cache_version()
        cache_key = f'leaderboard:{metric}:limit:{limit}:v{version}'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        payload = builder()
        cache.set(cache_key, payload, 30)
        return Response(payload)

    @action(detail=False, methods=['get'])
    def reputation(self, request):
        limit = min(int(request.query_params.get('limit', 50)), 100)
        return self._cache_response(
            'reputation',
            limit,
            lambda: [
                self._serialize_profile(profile, idx)
                for idx, profile in enumerate(
                    UserProfile.objects.all().order_by('-reputation')[:limit],
                    1,
                )
            ],
        )

    @action(detail=False, methods=['get'])
    def engagement(self, request):
        limit = min(int(request.query_params.get('limit', 50)), 100)
        return self._cache_response(
            'engagement',
            limit,
            lambda: [
                self._serialize_profile(profile, idx, {'total_engagement': getattr(profile, 'post_count', 0)})
                for idx, profile in enumerate(
                    UserProfile.objects.annotate(post_count=Count('post')).order_by('-post_count')[:limit],
                    1,
                )
            ],
        )

    @action(detail=False, methods=['get'])
    def activity(self, request):
        return self.engagement(request)

    @action(detail=False, methods=['get'])
    def points(self, request):
        limit = min(int(request.query_params.get('limit', 50)), 100)
        try:
            def build_points():
                wallets = Wallet.objects.select_related('user').order_by('-httn_points')[:limit]
                ranked = []
                for idx, wallet in enumerate(wallets, 1):
                    try:
                        profile = wallet.user
                        ranked.append(
                            self._serialize_profile(profile, idx, {
                                'httn_points': wallet.httn_points,
                            })
                        )
                    except Exception:
                        continue
                return ranked

            return self._cache_response('points', limit, build_points)
        except Exception:
            return self.reputation(request)

    @action(detail=False, methods=['get'])
    def earnings(self, request):
        return self.points(request)

    @action(detail=False, methods=['get'])
    def me(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            rep = profile.reputation or 0
            rank = UserProfile.objects.filter(reputation__gt=rep).count() + 1
            total = UserProfile.objects.count()
            percentile = round(((total - rank) / max(total, 1)) * 100, 1)
            return Response({
                'rank': rank,
                'reputation': rep,
                'percentile': percentile,
                'total_users': total,
            })
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)
