from rest_framework import views, permissions
from rest_framework.response import Response
from django.contrib.auth.models import User as DjangoUser
from users.models import User as UserProfile
from users.models import DirectMessage
from posts.models import Post
from wallets.models import Wallet
from livestreams.models import LiveStream
from django.db.models import Count, Sum, F
from django.db.models import Q
from django.db.models.functions import TruncDate
from adminpanel.permissions import (
    CanBanUsers,
    CanViewAnalytics,
    CanViewPosts,
    CanViewUsers,
)
from .permissions import build_admin_context


class AdminStatsView(views.APIView):
    """Admin dashboard statistics"""
    permission_classes = [CanViewAnalytics]
    
    def get(self, request):
        # Get total counts
        total_users = UserProfile.objects.count()
        total_posts = Post.objects.count()
        total_wallets = Wallet.objects.count()
        
        # Get today's active users
        from django.utils import timezone
        
        today = timezone.now().date()
        active_today = Post.objects.filter(
            created_at__date=today
        ).values('author_id').distinct().count()
        
        # Calculate total HTTN points
        total_httn = Wallet.objects.aggregate(
            total=Sum('httn_points')
        )['total'] or 0
        
        return Response({
            'total_users': total_users,
            'total_posts': total_posts,
            'active_users_today': active_today,
            'total_wallets': total_wallets,
            'total_httn_points': total_httn,
            'stats_collected_at': timezone.now()
        })


class AdminAnalyticsView(views.APIView):
    """Admin analytics payload for dashboard charts and top content."""
    permission_classes = [CanViewAnalytics]

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta

        try:
            window_days = int(request.query_params.get('days', 14))
        except (TypeError, ValueError):
            window_days = 14
        window_days = max(7, min(window_days, 90))

        today = timezone.now().date()
        start_date = today - timedelta(days=window_days - 1)

        def build_daily_map(queryset, field_name='count'):
            return {
                item['day'].isoformat(): item[field_name]
                for item in queryset
            }

        users_daily = build_daily_map(
            UserProfile.objects.filter(created_at__date__gte=start_date)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        posts_daily = build_daily_map(
            Post.objects.filter(created_at__date__gte=start_date)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        messages_daily = build_daily_map(
            DirectMessage.objects.filter(created_at__date__gte=start_date)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        streams_daily = build_daily_map(
            LiveStream.objects.filter(created_at__date__gte=start_date)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        series = []
        for offset in range(window_days):
            day = start_date + timedelta(days=offset)
            key = day.isoformat()
            series.append({
                'date': key,
                'users': users_daily.get(key, 0),
                'posts': posts_daily.get(key, 0),
                'messages': messages_daily.get(key, 0),
                'streams': streams_daily.get(key, 0),
            })

        engagement = Post.objects.aggregate(
            total_likes=Sum('likes_count'),
            total_comments=Sum('comments_count'),
            total_shares=Sum('shares_count'),
            total_views=Sum('views_count'),
        )

        top_posts = Post.objects.select_related('author_id').annotate(
            total_engagement=F('likes_count') + F('comments_count') + F('shares_count')
        ).order_by('-total_engagement', '-views_count', '-created_at')[:5]

        return Response({
            'window_days': window_days,
            'series': series,
            'engagement_totals': {
                'likes': engagement['total_likes'] or 0,
                'comments': engagement['total_comments'] or 0,
                'shares': engagement['total_shares'] or 0,
                'views': engagement['total_views'] or 0,
            },
            'top_posts': [
                {
                    'id': str(item.id),
                    'content': item.content,
                    'author_username': item.author_id.username,
                    'author_display_name': item.author_id.display_name,
                    'likes_count': item.likes_count,
                    'comments_count': item.comments_count,
                    'shares_count': item.shares_count,
                    'views_count': item.views_count,
                    'total_engagement': item.total_engagement,
                    'created_at': item.created_at,
                }
                for item in top_posts
            ],
            'generated_at': timezone.now(),
        })


class AdminUsersView(views.APIView):
    """Admin user management"""
    permission_classes = [CanViewUsers]
    
    def get(self, request):
        from users.serializers import UserProfileSerializer
        
        page = int(request.query_params.get('page', 1))
        limit = min(int(request.query_params.get('limit', 50)), 100)
        
        users = UserProfile.objects.all().order_by('-created_at')
        search = request.query_params.get('search')
        if search:
            users = users.filter(Q(username__icontains=search) | Q(display_name__icontains=search) | Q(email__icontains=search))
        
        start = (page - 1) * limit
        end = start + limit
        
        paginated_users = users[start:end]
        
        serialized = UserProfileSerializer(paginated_users, many=True).data
        admin_context_by_user_id = {
            str(item.id): build_admin_context(item.user_id)
            for item in paginated_users
        }
        for item in serialized:
            admin_context = admin_context_by_user_id.get(str(item['id']), {})
            item['admin_role'] = admin_context.get('role', 'user')
            item['is_admin'] = admin_context.get('is_admin', False)
            item['admin_permissions'] = admin_context.get('permissions', [])

        return Response({
            'data': serialized,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': users.count(),
                'total_pages': (users.count() + limit - 1) // limit if limit else 1
            }
        })


class AdminPostsView(views.APIView):
    """Admin post management"""
    permission_classes = [CanViewPosts]
    
    def get(self, request):
        from posts.serializers import PostSerializer
        
        page = int(request.query_params.get('page', 1))
        limit = min(int(request.query_params.get('limit', 50)), 100)
        
        posts = Post.objects.all().order_by('-created_at')
        search = request.query_params.get('search')
        if search:
            posts = posts.filter(content__icontains=search)
        
        start = (page - 1) * limit
        end = start + limit
        
        paginated_posts = posts[start:end]
        
        return Response({
            'data': PostSerializer(paginated_posts, many=True).data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': posts.count(),
                'total_pages': (posts.count() + limit - 1) // limit if limit else 1
            }
        })


class AdminBanUserView(views.APIView):
    """Ban a user"""
    permission_classes = [CanBanUsers]
    
    def post(self, request, user_id):
        try:
            profile = UserProfile.objects.get(id=user_id)
            reason = request.data.get('reason', 'Policy violation')
            duration_days = request.data.get('duration_days', 30)
            
            profile.user_id.is_active = False
            profile.user_id.save()
            
            from django.utils import timezone
            from datetime import timedelta
            
            banned_until = timezone.now() + timedelta(days=duration_days)
            
            return Response({
                'success': True,
                'message': f'User {profile.username} banned',
                'reason': reason,
                'banned_until': banned_until
            })
            
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
