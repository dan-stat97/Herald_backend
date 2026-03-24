from rest_framework.decorators import api_view
from rest_framework.response import Response


def _url(request, path):
    """Build an absolute URL from a path."""
    return request.build_absolute_uri(f'/api/v1{path}')


@api_view(['GET'])
def api_root(request, format=None):
    """
    Herald Backend API v1 — Root Endpoint
    All endpoints use JWT Bearer Token authentication unless marked [public].
    """
    b = request.build_absolute_uri   # noqa: shorthand

    return Response({
        'message': 'Welcome to Herald Backend API v1',
        'version': '1.0.0',
        'authentication': 'JWT Bearer Token  —  Authorization: Bearer <access_token>',
        'base_url': _url(request, '/'),

        # ── Health ────────────────────────────────────────────────────────────
        'health': {
            '_note': '[public]',
            'api':  _url(request, '/health/'),
            'db':   _url(request, '/health/db/'),
            'auth': _url(request, '/health/auth/'),
        },

        # ── Authentication ────────────────────────────────────────────────────
        'auth': {
            '_note': '[public] except current_user',
            'signup':       _url(request, '/auth/signup/'),
            'signin':       _url(request, '/auth/signin/'),
            'signout':      _url(request, '/auth/signout/'),
            'token_refresh': _url(request, '/auth/token/refresh/'),
            'current_user': _url(request, '/auth/users/profiles/me/'),
            'change_password': _url(request, '/auth/users/set_password/'),
        },

        # ── Users ─────────────────────────────────────────────────────────────
        'users': {
            'list':             _url(request, '/users/'),
            'me':               _url(request, '/users/me/'),
            'me_stats':         _url(request, '/users/me/stats/'),
            'me_avatar':        _url(request, '/users/me/avatar/'),
            'me_settings':      _url(request, '/users/me/settings/'),
            'me_posts':         _url(request, '/users/me/posts/'),
            'me_tasks':         _url(request, '/users/me/tasks/'),
            'me_earnings':      _url(request, '/users/me/earnings/'),
            'me_communities':   _url(request, '/users/me/communities/'),
            'me_interests':     _url(request, '/users/me/interests/'),
            'by_username':      '/api/v1/users/by-username/{username}/',
            'detail':           '/api/v1/users/{user_id}/',
            'stats_by_id':      '/api/v1/users/{user_id}/stats/',
            'posts_by_id':      '/api/v1/users/{user_id}/posts/',
            'tasks_by_id':      '/api/v1/users/{user_id}/tasks/',
            'search':           _url(request, '/users/search/'),
            'suggestions':      _url(request, '/users/suggestions/'),
            'follow':           '/api/v1/users/{user_id}/follow/',
            'unfollow':         '/api/v1/users/{user_id}/unfollow/',
            'followers':        '/api/v1/users/{user_id}/followers/',
            'following':        '/api/v1/users/{user_id}/following/',
            'follow_check':     _url(request, '/follow/check/'),
            'bulk_follow':      _url(request, '/users/me/follows/bulk/'),
            'onboarding_complete': _url(request, '/users/me/onboarding/complete/'),
        },

        # ── Posts ─────────────────────────────────────────────────────────────
        'posts': {
            '_note': 'list/retrieve [public], write requires auth',
            'list':             _url(request, '/posts/'),
            'detail':           '/api/v1/posts/{post_id}/',
            'create':           _url(request, '/posts/'),
            'trending':         _url(request, '/posts/trending/'),
            'following':        _url(request, '/posts/following/'),
            'scheduled':        _url(request, '/posts/scheduled/'),
            'scheduled_mine':   _url(request, '/posts/scheduled/me/'),
            'like':             '/api/v1/posts/{post_id}/like/',
            'unlike':           '/api/v1/posts/{post_id}/unlike/',
            'share':            '/api/v1/posts/{post_id}/share/',
            'bookmark':         '/api/v1/posts/{post_id}/bookmark/',
            'unbookmark':       '/api/v1/posts/{post_id}/unbookmark/',
            'comments':         '/api/v1/posts/{post_id}/comments/',
            'search':           _url(request, '/search/posts/'),
        },

        # ── Comments ──────────────────────────────────────────────────────────
        'comments': {
            'list':    _url(request, '/comments/'),
            'detail':  '/api/v1/comments/{comment_id}/',
            'create':  _url(request, '/comments/'),
            'like':    '/api/v1/comments/{comment_id}/like/',
        },

        # ── Notifications ─────────────────────────────────────────────────────
        'notifications': {
            'list':          _url(request, '/notifications/'),
            'detail':        '/api/v1/notifications/{notification_id}/',
            'mark_read':     '/api/v1/notifications/{notification_id}/mark_as_read/',
            'mark_all_read': _url(request, '/notifications/mark-all-read/'),
            'clear_all':     _url(request, '/notifications/clear-all/'),
        },

        # ── Bookmarks ─────────────────────────────────────────────────────────
        'bookmarks': {
            'mine':       _url(request, '/bookmarks/my/'),
            'bookmark':   '/api/v1/posts/{post_id}/bookmark/',
            'unbookmark': '/api/v1/posts/{post_id}/unbookmark/',
        },

        # ── Wallets ───────────────────────────────────────────────────────────
        'wallets': {
            'mine':         _url(request, '/wallets/me/'),
            'transactions': _url(request, '/wallets/me/transactions/'),
            'convert':      _url(request, '/wallets/me/convert/'),
            'withdraw':     _url(request, '/wallets/me/withdraw/'),
            'transfer':     _url(request, '/wallets/transfer/'),
        },

        # ── Leaderboard ───────────────────────────────────────────────────────
        'leaderboard': {
            '_note': '[public]',
            'by_reputation':  _url(request, '/leaderboard/reputation/'),
            'by_engagement':  _url(request, '/leaderboard/engagement/'),
            'by_points':      _url(request, '/leaderboard/points/'),
            'by_earnings':    _url(request, '/leaderboard/earnings/'),
            'by_activity':    _url(request, '/leaderboard/activity/'),
            'my_rank':        _url(request, '/leaderboard/me/'),
        },

        # ── News ──────────────────────────────────────────────────────────────
        'news': {
            '_note': '[public]',
            'list':     _url(request, '/news/'),
            'detail':   '/api/v1/news/{article_id}/',
            'like':     '/api/v1/news/{article_id}/like/',
            'bookmark': '/api/v1/news/{article_id}/bookmark/',
        },

        # ── Live Streams ──────────────────────────────────────────────────────
        'streams': {
            '_note': 'list/retrieve [public], write requires auth',
            'list':          _url(request, '/streams/'),
            'detail':        '/api/v1/streams/{stream_id}/',
            'create':        _url(request, '/streams/'),
            'chat':          '/api/v1/streams/{stream_id}/chat/',
            'donations':     '/api/v1/streams/{stream_id}/donations/',
            'viewer_join':   '/api/v1/streams/{stream_id}/viewer-join/',
            'viewer_leave':  '/api/v1/streams/{stream_id}/viewer-leave/',
        },

        # ── Communities ───────────────────────────────────────────────────────
        'communities': {
            '_note': '[public]',
            'list':   _url(request, '/communities/'),
            'detail': '/api/v1/communities/{community_id}/',
            'join':   '/api/v1/communities/{community_id}/join/',
        },

        # ── Causes ────────────────────────────────────────────────────────────
        'causes': {
            '_note': '[public]',
            'list':   _url(request, '/causes/'),
            'detail': '/api/v1/causes/{cause_id}/',
        },

        # ── Tasks ─────────────────────────────────────────────────────────────
        'tasks': {
            'list':        _url(request, '/tasks/'),
            'detail':      '/api/v1/tasks/{task_id}/',
            'mine':        _url(request, '/users/me/tasks/'),
            'claim_mine':  '/api/v1/users/me/tasks/{task_id}/claim/',
            'claim':       '/api/v1/users/{user_id}/tasks/{task_id}/claim/',
        },

        # ── Ads ───────────────────────────────────────────────────────────────
        'ads': {
            'active_ads':      _url(request, '/ads/active/'),
            'click_ad':        '/api/v1/ads/active/{campaign_id}/click/',
            'my_campaigns':    _url(request, '/ads/campaigns/'),
            'campaign_detail': '/api/v1/ads/campaigns/{campaign_id}/',
        },

        # ── E-Store ───────────────────────────────────────────────────────────
        'store': {
            '_note': '[public browse]',
            'products':       _url(request, '/products/'),
            'product_detail': '/api/v1/products/{product_id}/',
            'orders':         _url(request, '/orders/'),
            'order_detail':   '/api/v1/orders/{order_id}/',
            'cart':           _url(request, '/cart/'),
            'cart_items':     _url(request, '/cart/items/'),
            'store_products': _url(request, '/store/products/'),
            'checkout':       _url(request, '/store/checkout/'),
            'my_orders':      _url(request, '/store/orders/me/'),
        },

        # ── Media ─────────────────────────────────────────────────────────────
        'media': {
            'upload': _url(request, '/media/upload/'),
        },

        # ── Search & Discovery ────────────────────────────────────────────────
        'search': {
            '_note': '[public]',
            'users':           _url(request, '/search/users/'),
            'posts':           _url(request, '/search/posts/'),
            'trending_topics': _url(request, '/trending/topics/'),
        },

        # ── Messaging ─────────────────────────────────────────────────────────
        'messages': {
            'conversations':       _url(request, '/messages/conversations/'),
            'conversation_detail': '/api/v1/messages/conversations/{user_id}/',
            'create_message':      _url(request, '/messages/'),
            'mark_read':           '/api/v1/messages/{message_id}/read/',
            'unread_count':        _url(request, '/messages/unread-count/'),
        },

        # ── AI ────────────────────────────────────────────────────────────────
        'ai': {
            'posting_suggestions': _url(request, '/ai/posting-time-suggestions/'),
            'content_insights':    _url(request, '/ai/content-insights/'),
        },

        # ── Admin (is_staff required) ─────────────────────────────────────────
        'admin': {
            '_note': 'Requires is_staff=True',
            'my_role':        _url(request, '/admin/me/role/'),
            'stats':          _url(request, '/admin/stats/'),
            'users':          _url(request, '/admin/users/'),
            'verify_user':    '/api/v1/admin/users/{user_id}/verify/',
            'ban_user':       '/api/v1/admin/users/{user_id}/ban/',
            'posts':          _url(request, '/admin/posts/'),
            'reports':        _url(request, '/admin/reports/'),
            'report_detail':  '/api/v1/admin/reports/{report_id}/',
            'ads':            _url(request, '/admin/ads/'),
            'ad_detail':      '/api/v1/admin/ads/{campaign_id}/',
        },

        # ── Summary ───────────────────────────────────────────────────────────
        'summary': {
            'total_endpoint_groups': 17,
            'authentication': 'JWT Bearer Token',
            'token_header': 'Authorization: Bearer <access_token>',
            'content_type': 'application/json',
            'trailing_slashes': 'optional (both /path/ and /path work)',
        },
    })
