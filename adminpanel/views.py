from rest_framework import views, permissions
from rest_framework.response import Response
from django.contrib.auth.models import User as DjangoUser
from users.models import User as UserProfile
from posts.models import Post
from wallets.models import Wallet
from django.db.models import Count, Sum
from django.db.models import Q


class AdminStatsView(views.APIView):
    """Admin dashboard statistics"""
    permission_classes = [permissions.IsAdminUser]
    
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


class AdminUsersView(views.APIView):
    """Admin user management"""
    permission_classes = [permissions.IsAdminUser]
    
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
        
        return Response({
            'data': UserProfileSerializer(paginated_users, many=True).data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': users.count(),
                'total_pages': (users.count() + limit - 1) // limit if limit else 1
            }
        })


class AdminPostsView(views.APIView):
    """Admin post management"""
    permission_classes = [permissions.IsAdminUser]
    
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
    permission_classes = [permissions.IsAdminUser]
    
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
