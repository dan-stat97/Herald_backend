# core/leaderboard_views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum
from .models import Profiles, Posts, Wallets
from .serializers import ProfileSerializer
from .pagination import StandardPagination
from datetime import timedelta
from django.utils import timezone

class LeaderboardViewSet(viewsets.GenericViewSet):
    """
    Leaderboard functionality
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    @action(detail=False, methods=['get'])
    def reputation(self, request):
        """Get top users by reputation/balance"""
        queryset = Profiles.objects.all().order_by('-balance')[:100]
        
        # Add rank
        ranked_users = []
        for idx, user in enumerate(queryset, 1):
            user_data = ProfileSerializer(user, context={'request': request}).data
            user_data['rank'] = idx
            ranked_users.append(user_data)
        
        return Response(ranked_users)
    
    @action(detail=False, methods=['get'])
    def activity(self, request):
        """Get top users by activity (posts + likes received)"""
        period = request.query_params.get('period', 'all_time')
        
        # Date filtering
        if period == 'week':
            start_date = timezone.now() - timedelta(days=7)
        elif period == 'month':
            start_date = timezone.now() - timedelta(days=30)
        else:
            start_date = None
        
        # Annotate users with post count
        queryset = Profiles.objects.all()
        
        if start_date:
            queryset = queryset.annotate(
                post_count=Count('posts', filter=Posts.objects.filter(created_at__gte=start_date))
            ).order_by('-post_count')[:100]
        else:
            queryset = queryset.annotate(
                post_count=Count('posts')
            ).order_by('-post_count')[:100]
        
        # Add rank
        ranked_users = []
        for idx, user in enumerate(queryset, 1):
            user_data = ProfileSerializer(user, context={'request': request}).data
            user_data['rank'] = idx
            user_data['post_count'] = user.post_count
            ranked_users.append(user_data)
        
        return Response(ranked_users)

    @action(detail=False, methods=['get'])
    def engagement(self, request):
        """Alias endpoint for engagement leaderboard"""
        return self.activity(request)
    
    @action(detail=False, methods=['get'])
    def earnings(self, request):
        """Get top users by HTTN earned"""
        queryset = Wallets.objects.all().order_by('-httn_points')[:100]
        
        ranked_users = []
        for idx, wallet in enumerate(queryset, 1):
            try:
                profile = Profiles.objects.get(user_id=wallet.user_id)
                user_data = ProfileSerializer(profile, context={'request': request}).data
                user_data['rank'] = idx
                user_data['httn_points'] = wallet.httn_points
                user_data['httn_tokens'] = str(wallet.httn_tokens)
                ranked_users.append(user_data)
            except Profiles.DoesNotExist:
                continue
        
        return Response(ranked_users)

    @action(detail=False, methods=['get'])
    def points(self, request):
        """Alias endpoint for points leaderboard"""
        return self.earnings(request)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's rank"""
        try:
            profile = Profiles.objects.get(user_id=request.user.id)
            
            # Calculate rank by reputation
            higher_users = Profiles.objects.filter(balance__gt=profile.balance).count()
            rank = higher_users + 1
            total_users = Profiles.objects.count()
            percentile = ((total_users - rank) / total_users) * 100
            
            return Response({
                'rank': rank,
                'reputation': profile.balance or 0,
                'percentile': round(percentile, 1),
                'total_users': total_users
            })
            
        except Profiles.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)