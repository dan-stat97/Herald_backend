from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    """
    Herald Backend API v1 - Root Endpoint
    
    Available API endpoints:
    """
    return Response({
        'message': 'Welcome to Herald Backend API v1',
        'version': '1.0.0',
        'documentation': {
            'auth': {
                'signup': reverse('auth-signup', request=request, format=format),
                'signin': reverse('auth-signin', request=request, format=format),
                'signout': reverse('auth-signout', request=request, format=format),
                'refresh': reverse('auth-refresh', request=request, format=format),
                'current_user': reverse('auth-user', request=request, format=format),
            },
            'users': {
                'profiles_list': request.build_absolute_uri('/api/v1/profiles/'),
                'profiles_me': request.build_absolute_uri('/api/v1/auth/users/profiles/me/'),
                'follow_user': '/api/v1/users/{user_id}/follow/',
                'unfollow_user': '/api/v1/users/{user_id}/unfollow/',
                'user_followers': '/api/v1/users/{user_id}/followers/',
                'user_following': '/api/v1/users/{user_id}/following/',
                'check_follow': '/api/v1/follow/check/',
            },
            'posts': {
                'posts_list': request.build_absolute_uri('/api/v1/posts/'),
                'post_detail': '/api/v1/posts/{post_id}/',
                'create_post': request.build_absolute_uri('/api/v1/posts/'),
                'like_post': '/api/v1/posts/{post_id}/like/',
                'unlike_post': '/api/v1/posts/{post_id}/unlike/',
            },
            'comments': {
                'comments_list': request.build_absolute_uri('/api/v1/comments/'),
                'comment_detail': '/api/v1/comments/{comment_id}/',
                'create_comment': request.build_absolute_uri('/api/v1/comments/'),
            },
            'notifications': {
                'notifications_list': request.build_absolute_uri('/api/v1/notifications/'),
                'mark_as_read': '/api/v1/notifications/{notification_id}/mark_as_read/',
                'mark_all_as_read': request.build_absolute_uri('/api/v1/notifications/mark_all_as_read/'),
            },
            'bookmarks': {
                'my_bookmarks': request.build_absolute_uri('/api/v1/bookmarks/my/'),
                'bookmark_post': '/api/v1/posts/{post_id}/bookmark/',
                'unbookmark_post': '/api/v1/posts/{post_id}/unbookmark/',
            },
            'wallets': {
                'my_wallet': request.build_absolute_uri('/api/v1/wallets/me/'),
                'wallet_balance': request.build_absolute_uri('/api/v1/wallets/me/balance/'),
                'wallet_transactions': request.build_absolute_uri('/api/v1/wallets/me/transactions/'),
            },
            'leaderboard': {
                'reputation': request.build_absolute_uri('/api/v1/leaderboard/reputation/'),
                'activity': request.build_absolute_uri('/api/v1/leaderboard/activity/'),
                'earnings': request.build_absolute_uri('/api/v1/leaderboard/earnings/'),
                'my_rank': request.build_absolute_uri('/api/v1/leaderboard/me/'),
            },
            'communities': {
                'communities_list': request.build_absolute_uri('/api/v1/communities/'),
                'community_detail': '/api/v1/communities/{community_id}/',
            },
            'causes': {
                'causes_list': request.build_absolute_uri('/api/v1/causes/'),
                'cause_detail': '/api/v1/causes/{cause_id}/',
            },
        },
        'endpoints_summary': {
            'total_endpoints': '50+',
            'authentication': 'JWT Bearer Token',
            'base_url': request.build_absolute_uri('/api/v1/'),
        }
    })
