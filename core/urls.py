# Post interaction endpoints (handled in urlpatterns below if needed)
from posts.interactions import PostLikeView, PostShareView, PostBookmarkView
# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileViewSet, LikeViewSet, RepostViewSet,
    HashtagViewSet, TransactionViewSet, NewsViewSet,
    CommunityViewSet, CauseViewSet
)
from notifications.views import NotificationViewSet
from posts.views import PostViewSet
from wallets.views import WalletViewSet
from wallets.transfer import WalletTransferView
from wallets.advanced import WalletTransactionsView, WalletConvertView, WalletWithdrawView
from posts.comments import CommentViewSet
from users.follows import FollowViewSet
from users.views import UserProfileViewSet, UserByUsernameView, UserPostsView, UserTasksView, ClaimTaskRewardView
from users.extra_views import (
    UserSuggestionsView,
    UserSearchView,
    UserSettingsView,
    UserEarningsView,
    UserAnalyticsEngagementSeriesView,
    UserAnalyticsAudienceBreakdownView,
    UserStatsByIdView,
    UserMeCommunitiesView,
    UserTaskClaimMeView,
    UserInterestsView,
    UserBulkFollowView,
    UserOnboardingCompleteView,
)
from users.avatar import AvatarUploadView
from .social_views import BookmarkViewSet
from .leaderboard_views import LeaderboardViewSet
from .auth_views import signup, signout, current_user
from .api_root import api_root
from .frontend_views import ApiHealthView, ApiHealthDbView, ApiHealthAuthView, TrendingTopicsView, SearchPostsView
from .feature_stub_views import (
    ConversationsView,
    ConversationDetailView,
    MessageCreateView,
    MessageReadView,
    MessageUnreadCountView,
    MediaUploadView,
    ScheduledPostsView,
    ScheduledPostsMeView,
    AiPostingSuggestionsView,
    StreamChatView,
    StreamDonationsView,
    StreamViewerJoinLeaveView,
    AiContentInsightsView,
)
from .news_interactions import NewsLikeView, NewsBookmarkView
from communities.joins import CommunityJoinView
from causes.views import CauseViewSet as CausesViewSet
from tasks.views import TaskViewSet
from livestreams.views import LiveStreamViewSet
from estore.views import ProductViewSet, OrderViewSet
from estore.cart import CartView, CartItemView
from estore.store_views import StoreProductsView, StoreCheckoutView, StoreOrdersMeView
from adminpanel.views import AdminStatsView, AdminUsersView, AdminPostsView, AdminBanUserView
from adminpanel.reports import AdminReportView, AdminReportDetailView
from adminpanel.extra_views import AdminRoleView, AdminVerifyUserView, AdCampaignListCreateView, AdCampaignDetailView

# Create v1 router
router_v1 = DefaultRouter(trailing_slash='/?')
router_v1.register(r'profiles', ProfileViewSet)
router_v1.register(r'posts', PostViewSet, basename='post')
router_v1.register(r'wallets', WalletViewSet, basename='wallet')
router_v1.register(r'likes', LikeViewSet)
router_v1.register(r'reposts', RepostViewSet)
router_v1.register(r'hashtags', HashtagViewSet)
router_v1.register(r'transactions', TransactionViewSet)
router_v1.register(r'news', NewsViewSet)
router_v1.register(r'communities', CommunityViewSet)
router_v1.register(r'causes', CausesViewSet, basename='cause')
router_v1.register(r'notifications', NotificationViewSet, basename='notification')
router_v1.register(r'comments', CommentViewSet, basename='comment')
router_v1.register(r'bookmarks', BookmarkViewSet, basename='bookmark')
router_v1.register(r'tasks', TaskViewSet, basename='task')
router_v1.register(r'streams', LiveStreamViewSet, basename='livestream')
router_v1.register(r'products', ProductViewSet, basename='product')
router_v1.register(r'orders', OrderViewSet, basename='order')

# Follow endpoints (custom routes)
follow_list = FollowViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

urlpatterns = [
    # API Root - Documentation
    path('v1/', api_root, name='api-root'),
    path('v1/health/', ApiHealthView.as_view(), name='api-health'),
    path('v1/health/db/', ApiHealthDbView.as_view(), name='api-health-db'),
    path('v1/health/auth/', ApiHealthAuthView.as_view(), name='api-health-auth'),
    path('v1/trending/topics/', TrendingTopicsView.as_view(), name='trending-topics'),
    path('v1/search/users/', UserSearchView.as_view(), name='search-users'),
    path('v1/search/posts/', SearchPostsView.as_view(), name='search-posts'),
    
    # Auth endpoints (from users app)
    path('v1/auth/', include('users.urls')),
    
    # Main v1 API endpoints
    path('v1/', include(router_v1.urls)),

    # Document-compatible users endpoints
    path('v1/users/', UserProfileViewSet.as_view({'get': 'list'}), name='users-list'),
    path('v1/users', UserProfileViewSet.as_view({'get': 'list'}), name='users-list-no-slash'),
    path('v1/users/suggestions/', UserSuggestionsView.as_view(), name='users-suggestions'),
    path('v1/users/suggested/', UserSuggestionsView.as_view(), name='users-suggested'),
    path('v1/users/search/', UserSearchView.as_view(), name='users-search'),
    path('v1/users/me/', UserProfileViewSet.as_view({'get': 'me', 'patch': 'me', 'delete': 'me'}), name='users-me'),
    path('v1/users/me/stats/', UserProfileViewSet.as_view({'get': 'stats'}), name='users-me-stats'),
    path('v1/users/me/settings/', UserSettingsView.as_view(), name='users-me-settings'),
    path('v1/users/me/posts/', UserPostsView.as_view(), name='users-me-posts'),
    path('v1/users/me/tasks/', UserTasksView.as_view(), name='users-me-tasks'),
    path('v1/users/me/tasks/<uuid:task_id>/claim/', UserTaskClaimMeView.as_view(), name='users-me-task-claim'),
    path('v1/users/me/earnings/', UserEarningsView.as_view(), name='users-me-earnings'),
    path('v1/users/me/analytics/engagement-series/', UserAnalyticsEngagementSeriesView.as_view(), name='users-me-engagement-series'),
    path('v1/users/me/analytics/audience-breakdown/', UserAnalyticsAudienceBreakdownView.as_view(), name='users-me-audience-breakdown'),
    path('v1/users/me/communities/', UserMeCommunitiesView.as_view(), name='users-me-communities'),
    path('v1/users/me/interests/', UserInterestsView.as_view(), name='users-me-interests'),
    path('v1/users/me/follows/bulk/', UserBulkFollowView.as_view(), name='users-me-follows-bulk'),
    path('v1/users/me/onboarding/complete/', UserOnboardingCompleteView.as_view(), name='users-me-onboarding-complete'),
    path('v1/users/by-username/<str:username>/', UserByUsernameView.as_view(), name='users-by-username'),
    path('v1/users/<uuid:pk>/', UserProfileViewSet.as_view({'get': 'retrieve'}), name='users-detail'),
    path('v1/users/<uuid:pk>/stats/', UserStatsByIdView.as_view(), name='users-stats'),
    path('v1/users/<uuid:pk>/posts/', UserPostsView.as_view(), name='users-posts'),
    path('v1/users/<uuid:pk>/tasks/', UserTasksView.as_view(), name='users-tasks'),
    path('v1/users/<uuid:pk>/tasks/<uuid:task_id>/claim/', ClaimTaskRewardView.as_view(), name='users-task-claim'),
    
    # Follow endpoints
    path('v1/users/<uuid:pk>/follow/', FollowViewSet.as_view({'post': 'follow', 'delete': 'unfollow'}), name='user-follow'),
    path('v1/users/<uuid:pk>/unfollow/', FollowViewSet.as_view({'delete': 'unfollow'}), name='user-unfollow'),
    path('v1/users/<uuid:pk>/followers/', FollowViewSet.as_view({'get': 'followers'}), name='user-followers'),
    path('v1/users/<uuid:pk>/following/', FollowViewSet.as_view({'get': 'following'}), name='user-following'),
    path('v1/follow/check/', FollowViewSet.as_view({'get': 'check'}), name='follow-check'),
    path('v1/follows/<uuid:pk>/', FollowViewSet.as_view({'post': 'follow', 'delete': 'unfollow'}), name='follows-toggle'),
    path('v1/follows/status/<uuid:pk>/', FollowViewSet.as_view({'get': 'status'}), name='follows-status'),
    
    # Bookmark endpoints
    path('v1/posts/<uuid:pk>/bookmark/', BookmarkViewSet.as_view({'post': 'bookmark'}), name='post-bookmark'),
    path('v1/posts/<uuid:pk>/unbookmark/', BookmarkViewSet.as_view({'post': 'unbookmark'}), name='post-unbookmark'),
    path('v1/bookmarks/my/', BookmarkViewSet.as_view({'get': 'my_bookmarks'}), name='my-bookmarks'),
    
    # Leaderboard endpoints
    path('v1/leaderboard/reputation/', LeaderboardViewSet.as_view({'get': 'reputation'}), name='leaderboard-reputation'),
    path('v1/leaderboard/activity/', LeaderboardViewSet.as_view({'get': 'activity'}), name='leaderboard-activity'),
    path('v1/leaderboard/engagement/', LeaderboardViewSet.as_view({'get': 'engagement'}), name='leaderboard-engagement'),
    path('v1/leaderboard/earnings/', LeaderboardViewSet.as_view({'get': 'earnings'}), name='leaderboard-earnings'),
    path('v1/leaderboard/points/', LeaderboardViewSet.as_view({'get': 'points'}), name='leaderboard-points'),
    path('v1/leaderboard/me/', LeaderboardViewSet.as_view({'get': 'me'}), name='leaderboard-me'),
    path('v1/notifications/mark-all-read/', NotificationViewSet.as_view({'post': 'mark_all_read'}), name='notifications-mark-all-read'),
    path('v1/notifications/clear-all/', NotificationViewSet.as_view({'delete': 'clear_all'}), name='notifications-clear-all'),
    path('v1/posts/<pk>/like/', PostViewSet.as_view({'post': 'like', 'delete': 'unlike'}), name='post-like'),
    path('v1/posts/<pk>/unlike/', PostViewSet.as_view({'post': 'unlike'}), name='post-unlike'),
    path('v1/posts/<uuid:post_id>/comments/', CommentViewSet.as_view({'get': 'list', 'post': 'create'}), name='post-comments'),
    path('v1/comments/<uuid:pk>/like/', CommentViewSet.as_view({'post': 'like'}), name='comment-like'),
    
    # New wallet and user endpoints
    path('v1/wallets/transfer/', WalletTransferView.as_view(), name='wallet-transfer'),
    path('v1/users/me/avatar/', AvatarUploadView.as_view(), name='user-avatar'),
    
    # Communities join/leave endpoints  
    path('v1/communities/<uuid:community_id>/join/', CommunityJoinView.as_view(), name='community-join'),
    
    # Admin endpoints
    path('v1/admin/me/role/', AdminRoleView.as_view(), name='admin-role'),
    path('v1/admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('v1/admin/dashboard/stats/', AdminStatsView.as_view(), name='admin-dashboard-stats'),
    path('v1/admin/users/', AdminUsersView.as_view(), name='admin-users'),
    path('v1/admin/users/<uuid:user_id>/verify/', AdminVerifyUserView.as_view(), name='admin-verify-user'),
    path('v1/admin/posts/', AdminPostsView.as_view(), name='admin-posts'),
    path('v1/admin/users/<uuid:user_id>/ban/', AdminBanUserView.as_view(), name='admin-ban-user'),
    path('v1/admin/reports/', AdminReportView.as_view(), name='admin-reports'),
    path('v1/admin/reports/<uuid:report_id>/', AdminReportDetailView.as_view(), name='admin-report-detail'),

    # Ads endpoints
    path('v1/ads/campaigns/', AdCampaignListCreateView.as_view(), name='ads-campaigns'),
    path('v1/ads/campaigns/me/', AdCampaignListCreateView.as_view(), name='ads-campaigns-me'),
    path('v1/ads/campaigns/<uuid:campaign_id>/', AdCampaignDetailView.as_view(), name='ads-campaign-detail'),
    
    # Cart endpoints
    path('v1/cart/', CartView.as_view(), name='cart'),
    path('v1/cart/items/', CartItemView.as_view(), name='cart-items'),
    path('v1/cart/items/<uuid:product_id>/', CartItemView.as_view(), name='cart-item-delete'),

    # Store aliases
    path('v1/store/products/', StoreProductsView.as_view(), name='store-products'),
    path('v1/store/checkout/', StoreCheckoutView.as_view(), name='store-checkout'),
    path('v1/store/orders/me/', StoreOrdersMeView.as_view(), name='store-orders-me'),
    
    # Wallet advanced endpoints
    path('v1/wallets/me/transactions/', WalletTransactionsView.as_view(), name='wallet-transactions'),
    path('v1/wallets/me/convert/', WalletConvertView.as_view(), name='wallet-convert'),
    path('v1/wallets/me/withdraw/', WalletWithdrawView.as_view(), name='wallet-withdraw'),
    
    # News interaction endpoints
    path('v1/news/<uuid:article_id>/like/', NewsLikeView.as_view(), name='news-like'),
    path('v1/news/<uuid:article_id>/bookmark/', NewsBookmarkView.as_view(), name='news-bookmark'),

    # Messaging and shared feature endpoints
    path('v1/messages/conversations/', ConversationsView.as_view(), name='messages-conversations'),
    path('v1/messages/conversations/<uuid:user_id>/', ConversationDetailView.as_view(), name='messages-conversation-detail'),
    path('v1/messages/', MessageCreateView.as_view(), name='messages-create'),
    path('v1/messages/<uuid:message_id>/read/', MessageReadView.as_view(), name='messages-read'),
    path('v1/messages/unread-count/', MessageUnreadCountView.as_view(), name='messages-unread-count'),
    path('v1/media/upload/', MediaUploadView.as_view(), name='media-upload'),
    path('v1/posts/scheduled/', ScheduledPostsView.as_view(), name='posts-scheduled-create'),
    path('v1/posts/scheduled/me/', ScheduledPostsMeView.as_view(), name='posts-scheduled-me'),
    path('v1/ai/posting-time-suggestions/', AiPostingSuggestionsView.as_view(), name='ai-posting-time-suggestions'),
    path('v1/ai/content-insights/', AiContentInsightsView.as_view(), name='ai-content-insights'),

    # Live stream internals compatibility routes
    path('v1/streams/<uuid:stream_id>/chat/', StreamChatView.as_view(), name='stream-chat'),
    path('v1/streams/<uuid:stream_id>/donations/', StreamDonationsView.as_view(), name='stream-donations'),
    path('v1/streams/<uuid:stream_id>/viewer-join/', StreamViewerJoinLeaveView.as_view(), name='stream-viewer-join'),
    path('v1/streams/<uuid:stream_id>/viewer-leave/', StreamViewerJoinLeaveView.as_view(), name='stream-viewer-leave'),
]