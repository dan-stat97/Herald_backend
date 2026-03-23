# core/leaderboard_views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone

# Use the real UserProfile model (users_user table in production)
from users.models import User as UserProfile
from users.serializers import UserProfileSerializer
from wallets.models import Wallet


class LeaderboardViewSet(viewsets.GenericViewSet):
    """Leaderboard endpoints — public read access"""
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

    @action(detail=False, methods=['get'])
    def reputation(self, request):
        """Top users by reputation score"""
        limit = min(int(request.query_params.get('limit', 50)), 100)
        queryset = UserProfile.objects.all().order_by('-reputation')[:limit]
        ranked = [self._serialize_profile(u, idx) for idx, u in enumerate(queryset, 1)]
        return Response(ranked)

    @action(detail=False, methods=['get'])
    def engagement(self, request):
        """Top users by post count (engagement proxy)"""
        limit = min(int(request.query_params.get('limit', 50)), 100)
        queryset = (
            UserProfile.objects
            .annotate(post_count=Count('post'))
            .order_by('-post_count')[:limit]
        )
        ranked = [
            self._serialize_profile(u, idx, {'total_engagement': getattr(u, 'post_count', 0)})
            for idx, u in enumerate(queryset, 1)
        ]
        return Response(ranked)

    @action(detail=False, methods=['get'])
    def activity(self, request):
        return self.engagement(request)

    @action(detail=False, methods=['get'])
    def points(self, request):
        """Top users by HTTN wallet points"""
        limit = min(int(request.query_params.get('limit', 50)), 100)
        try:
            wallets = Wallet.objects.select_related('user').order_by('-httn_points')[:limit]
            ranked = []
            for idx, wallet in enumerate(wallets, 1):
                try:
                    profile = wallet.user
                    data = self._serialize_profile(profile, idx, {
                        'httn_points': wallet.httn_points,
                    })
                    ranked.append(data)
                except Exception:
                    continue
            return Response(ranked)
        except Exception:
            # Fallback: return reputation leaderboard if wallet table unavailable
            return self.reputation(request)

    @action(detail=False, methods=['get'])
    def earnings(self, request):
        return self.points(request)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Current user's rank by reputation"""
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
