# Herald Backend API Reference

This document is the current backend API reference for the Herald Django service.

- Base path: `/api/v1/`
- Auth: `Authorization: Bearer <access_token>` unless marked `Public`
- Trailing slash: optional on most endpoints
- Primary route sources:
  - [core/urls.py](/C:/Users/somto/Projects/Herald_backend/core/urls.py)
  - [users/urls.py](/C:/Users/somto/Projects/Herald_backend/users/urls.py)
  - [core/api_root.py](/C:/Users/somto/Projects/Herald_backend/core/api_root.py)

## Conventions

- `UUID` path params are shown as `{id}` style placeholders.
- Router-backed resources use Django REST Framework collection/detail routes.
- Some router resources also expose custom actions documented below.
- Public list/detail endpoints still enforce auth for write actions unless otherwise noted.

## Health

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/` | Public | API root and grouped endpoint index |
| `GET` | `/api/v1/health/` | Public | Basic API health |
| `GET` | `/api/v1/health/db/` | Public | Database health |
| `GET` | `/api/v1/health/auth/` | Public | Auth health |

## Authentication

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/signup/` | Public | Create account |
| `POST` | `/api/v1/auth/signin/` | Public | Sign in |
| `POST` | `/api/v1/auth/signout/` | Auth | Sign out |
| `POST` | `/api/v1/auth/refresh/` | Public | Refresh JWT/session token |
| `GET` | `/api/v1/auth/user/` | Auth | Current auth user |
| `GET` | `/api/v1/auth/session/` | Auth | Session info |
| `POST` | `/api/v1/auth/change-password/` | Auth | Change password |
| `POST` | `/api/v1/auth/password-reset/request/` | Public | Request password reset |
| `POST` | `/api/v1/auth/password-reset/confirm/` | Public | Confirm password reset |
| `GET` | `/api/v1/auth/kingschat/` | Public | Start KingsChat auth |
| `GET` | `/api/v1/auth/kingschat/callback/` | Public | KingsChat callback |
| `GET` | `/api/v1/auth/users/profiles/me/` | Auth | Current user profile alias |
| `GET` | `/api/v1/auth/users/profiles/me/posts/` | Auth | Current user posts alias |
| `GET` | `/api/v1/auth/users/profiles/me/tasks/` | Auth | Current user tasks alias |
| `POST` | `/api/v1/auth/users/profiles/me/tasks/{task_id}/claim/` | Auth | Claim task reward alias |

## Router-backed Resources

These resources are mounted through DRF routers. Collection/detail routes exist at the paths below.

| Resource | Collection | Detail |
| --- | --- | --- |
| Profiles | `/api/v1/profiles/` | `/api/v1/profiles/{id}/` |
| Posts | `/api/v1/posts/` | `/api/v1/posts/{id}/` |
| Wallets | `/api/v1/wallets/` | `/api/v1/wallets/{id}/` |
| Likes | `/api/v1/likes/` | `/api/v1/likes/{id}/` |
| Reposts | `/api/v1/reposts/` | `/api/v1/reposts/{id}/` |
| Hashtags | `/api/v1/hashtags/` | `/api/v1/hashtags/{id}/` |
| Transactions | `/api/v1/transactions/` | `/api/v1/transactions/{id}/` |
| News | `/api/v1/news/` | `/api/v1/news/{id}/` |
| Causes | `/api/v1/causes/` | `/api/v1/causes/{id}/` |
| Notifications | `/api/v1/notifications/` | `/api/v1/notifications/{id}/` |
| Comments | `/api/v1/comments/` | `/api/v1/comments/{id}/` |
| Bookmarks | `/api/v1/bookmarks/` | `/api/v1/bookmarks/{id}/` |
| Tasks | `/api/v1/tasks/` | `/api/v1/tasks/{id}/` |
| Streams | `/api/v1/streams/` | `/api/v1/streams/{id}/` |
| Products | `/api/v1/products/` | `/api/v1/products/{id}/` |
| Orders | `/api/v1/orders/` | `/api/v1/orders/{id}/` |
| Auth Profiles | `/api/v1/auth/users/` | `/api/v1/auth/users/{id}/` |

## Users

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/users/` | Public | List users |
| `GET` | `/api/v1/users` | Public | No-slash alias for user list |
| `GET` | `/api/v1/users/suggestions/` | Auth | User suggestions |
| `GET` | `/api/v1/users/suggested/` | Auth | Suggestions alias |
| `GET` | `/api/v1/users/search/` | Public | User search |
| `GET` | `/api/v1/users/me/` | Auth | Current profile |
| `PATCH` | `/api/v1/users/me/` | Auth | Update current profile |
| `DELETE` | `/api/v1/users/me/` | Auth | Delete current profile |
| `GET` | `/api/v1/users/me/stats/` | Auth | Current user stats |
| `GET` | `/api/v1/users/me/settings/` | Auth | Current user settings |
| `PATCH` | `/api/v1/users/me/settings/` | Auth | Update user settings |
| `GET` | `/api/v1/users/me/posts/` | Auth | Current user profile timeline |
| `GET` | `/api/v1/users/me/replies/` | Auth | Current user replies |
| `GET` | `/api/v1/users/me/tasks/` | Auth | Current user tasks |
| `POST` | `/api/v1/users/me/tasks/{task_id}/claim/` | Auth | Claim my task reward |
| `GET` | `/api/v1/users/me/earnings/` | Auth | Creator earnings |
| `GET` | `/api/v1/users/me/analytics/engagement-series/` | Auth | Engagement series |
| `GET` | `/api/v1/users/me/analytics/audience-breakdown/` | Auth | Audience breakdown |
| `GET` | `/api/v1/users/me/communities/` | Auth | My communities |
| `GET` | `/api/v1/users/me/interests/` | Auth | My interests |
| `PATCH` | `/api/v1/users/me/interests/` | Auth | Update interests |
| `POST` | `/api/v1/users/me/follows/bulk/` | Auth | Bulk follow/unfollow |
| `POST` | `/api/v1/users/me/onboarding/complete/` | Auth | Mark onboarding complete |
| `POST` | `/api/v1/users/me/avatar/` | Auth | Upload avatar |
| `POST` | `/api/v1/users/me/cover/` | Auth | Upload cover/banner |
| `GET` | `/api/v1/users/by-username/{username}/` | Public | Fetch user by username |
| `GET` | `/api/v1/users/{user_id}/` | Public | User detail |
| `GET` | `/api/v1/users/{user_id}/stats/` | Public | User stats |
| `GET` | `/api/v1/users/{user_id}/posts/` | Public | User profile timeline |
| `GET` | `/api/v1/users/{user_id}/replies/` | Public | User replies |
| `GET` | `/api/v1/users/{user_id}/tasks/` | Auth | User tasks |
| `POST` | `/api/v1/users/{user_id}/tasks/{task_id}/claim/` | Auth | Claim task reward |
| `POST` | `/api/v1/users/{user_id}/follow/` | Auth | Follow user |
| `DELETE` | `/api/v1/users/{user_id}/follow/` | Auth | Unfollow user via same route |
| `DELETE` | `/api/v1/users/{user_id}/unfollow/` | Auth | Explicit unfollow alias |
| `GET` | `/api/v1/users/{user_id}/followers/` | Public | Followers list |
| `GET` | `/api/v1/users/{user_id}/following/` | Public | Following list |
| `GET` | `/api/v1/follow/check/` | Auth | Follow state check |
| `POST` | `/api/v1/follows/{user_id}/` | Auth | Follow via alias |
| `DELETE` | `/api/v1/follows/{user_id}/` | Auth | Unfollow via alias |
| `GET` | `/api/v1/follows/status/{user_id}/` | Auth | Follow status |

## Posts

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/posts/` | Public | Main post feed / list |
| `POST` | `/api/v1/posts/` | Auth | Create post |
| `GET` | `/api/v1/posts/{post_id}/` | Public | Post detail |
| `PATCH` | `/api/v1/posts/{post_id}/` | Auth | Update post |
| `DELETE` | `/api/v1/posts/{post_id}/` | Auth | Delete post |
| `GET` | `/api/v1/posts/trending/` | Public | Trending posts |
| `GET` | `/api/v1/posts/following/` | Auth | Following-only feed |
| `POST` | `/api/v1/posts/{post_id}/like/` | Auth | Like post |
| `DELETE` | `/api/v1/posts/{post_id}/like/` | Auth | Unlike using same route |
| `POST` | `/api/v1/posts/{post_id}/unlike/` | Auth | Explicit unlike alias |
| `POST` | `/api/v1/posts/{post_id}/share/` | Auth | Repost/share post |
| `POST` | `/api/v1/posts/{post_id}/bookmark/` | Auth | Bookmark post |
| `POST` | `/api/v1/posts/{post_id}/unbookmark/` | Auth | Remove bookmark |
| `GET` | `/api/v1/posts/{post_id}/comments/` | Public | List post comments/replies |
| `POST` | `/api/v1/posts/{post_id}/comments/` | Auth | Create comment/reply |
| `POST` | `/api/v1/posts/scheduled/` | Auth | Create scheduled post |
| `GET` | `/api/v1/posts/scheduled/me/` | Auth | My scheduled posts |

## Comments / Replies

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/comments/` | Public | Comment list |
| `POST` | `/api/v1/comments/` | Auth | Create comment |
| `GET` | `/api/v1/comments/{comment_id}/` | Public | Comment detail |
| `DELETE` | `/api/v1/comments/{comment_id}/` | Auth | Delete own comment |
| `POST` | `/api/v1/comments/{comment_id}/like/` | Auth | Like comment |
| `POST` | `/api/v1/comments/{comment_id}/unlike/` | Auth | Unlike comment |
| `DELETE` | `/api/v1/comments/{comment_id}/unlike/` | Auth | Unlike alias |
| `POST` | `/api/v1/comments/{comment_id}/share/` | Auth | Repost/share comment |
| `POST` | `/api/v1/comments/{comment_id}/bookmark/` | Auth | Bookmark comment |
| `POST` | `/api/v1/comments/{comment_id}/unbookmark/` | Auth | Remove comment bookmark |
| `DELETE` | `/api/v1/comments/{comment_id}/unbookmark/` | Auth | Remove comment bookmark alias |

## Notifications

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/notifications/` | Auth | Notification list |
| `GET` | `/api/v1/notifications/{notification_id}/` | Auth | Notification detail |
| `POST` | `/api/v1/notifications/{notification_id}/mark_read/` | Auth | Mark notification read |
| `PATCH` | `/api/v1/notifications/{notification_id}/mark_read/` | Auth | Mark notification read |
| `POST` | `/api/v1/notifications/{notification_id}/mark_as_read/` | Auth | Compatibility alias |
| `POST` | `/api/v1/notifications/mark-all-read/` | Auth | Mark all read |
| `DELETE` | `/api/v1/notifications/clear-all/` | Auth | Delete all notifications |

## Bookmarks

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/bookmarks/my/` | Auth | Current user bookmarks |
| `POST` | `/api/v1/bookmarks/clear-all/` | Auth | Clear all bookmarks |

## Wallets

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/wallets/me/` | Auth | Get or create current wallet |
| `GET` | `/api/v1/wallets/me/transactions/` | Auth | Wallet transaction history |
| `POST` | `/api/v1/wallets/me/convert/` | Auth | Convert balances |
| `POST` | `/api/v1/wallets/me/withdraw/` | Auth | Withdraw Espees |
| `POST` | `/api/v1/wallets/transfer/` | Auth | Transfer `httn_points`, `httn_tokens`, or `espees` |

## Leaderboard

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/leaderboard/reputation/` | Public | Reputation leaderboard |
| `GET` | `/api/v1/leaderboard/activity/` | Public | Activity leaderboard |
| `GET` | `/api/v1/leaderboard/engagement/` | Public | Engagement leaderboard |
| `GET` | `/api/v1/leaderboard/earnings/` | Public | Earnings leaderboard |
| `GET` | `/api/v1/leaderboard/points/` | Public | Points leaderboard |
| `GET` | `/api/v1/leaderboard/me/` | Auth | Current user rank summary |

## News

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/news/` | Public | News/article list |
| `GET` | `/api/v1/news/{article_id}/` | Public | News/article detail |
| `GET` | `/api/v1/news/clusters/` | Public | Clustered news feed |
| `GET` | `/api/v1/news/{article_id}/context/` | Public | Context for a news article |
| `GET` | `/api/v1/news/bookmarks/me/` | Auth | My saved news articles |
| `POST` | `/api/v1/news/{article_id}/like/` | Auth | Like article |
| `POST` | `/api/v1/news/{article_id}/bookmark/` | Auth | Bookmark article |

## Live Streams

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/streams/` | Public | List streams |
| `POST` | `/api/v1/streams/` | Auth | Create stream |
| `GET` | `/api/v1/streams/{stream_id}/` | Public | Stream detail |
| `PATCH` | `/api/v1/streams/{stream_id}/` | Auth | Update stream |
| `POST` | `/api/v1/streams/{stream_id}/end/` | Auth | End owned stream |
| `GET` | `/api/v1/streams/{stream_id}/chat/` | Public | Stream chat messages |
| `POST` | `/api/v1/streams/{stream_id}/chat/` | Auth | Send chat message |
| `GET` | `/api/v1/streams/{stream_id}/donations/` | Public | Stream donations |
| `POST` | `/api/v1/streams/{stream_id}/donations/` | Auth | Donate to stream |
| `POST` | `/api/v1/streams/{stream_id}/viewer-join/` | Auth | Mark viewer joined |
| `POST` | `/api/v1/streams/{stream_id}/viewer-leave/` | Auth | Mark viewer left |

## Communities

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/communities/` | Public | List communities |
| `POST` | `/api/v1/communities/` | Auth | Create community |
| `GET` | `/api/v1/communities/{community_id}/` | Public | Community detail |
| `PATCH` | `/api/v1/communities/{community_id}/` | Auth | Update community |
| `DELETE` | `/api/v1/communities/{community_id}/` | Auth | Delete community |
| `POST` | `/api/v1/communities/{community_id}/join/` | Auth | Join community |
| `GET` | `/api/v1/communities/{community_id}/posts/` | Public | Community posts |
| `POST` | `/api/v1/communities/{community_id}/posts/` | Auth | Create community post |
| `POST` | `/api/v1/communities/{community_id}/posts/{post_id}/like/` | Auth | Like community post |
| `GET` | `/api/v1/communities/{community_id}/posts/{post_id}/comments/` | Public | Community post comments |
| `POST` | `/api/v1/communities/{community_id}/posts/{post_id}/comments/` | Auth | Add community comment |
| `POST` | `/api/v1/communities/{community_id}/posts/{post_id}/pin/` | Auth | Pin community post |
| `GET` | `/api/v1/communities/{community_id}/members/` | Public | Community members |
| `GET` | `/api/v1/communities/{community_id}/join-requests/` | Auth | Join requests |
| `GET` | `/api/v1/communities/{community_id}/join-requests/{request_id}/` | Auth | Join request detail |
| `PATCH` | `/api/v1/communities/{community_id}/join-requests/{request_id}/` | Auth | Review join request |
| `GET` | `/api/v1/communities/{community_id}/invites/` | Auth | Community invites |
| `POST` | `/api/v1/communities/{community_id}/invites/` | Auth | Create invite |
| `POST` | `/api/v1/communities/{community_id}/invites/{invite_id}/respond/` | Auth | Respond to invite |

## Causes

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/causes/` | Public | List causes |
| `POST` | `/api/v1/causes/` | Auth | Create cause |
| `GET` | `/api/v1/causes/{cause_id}/` | Public | Cause detail |
| `PATCH` | `/api/v1/causes/{cause_id}/` | Auth | Update cause |
| `DELETE` | `/api/v1/causes/{cause_id}/` | Auth | Delete cause |

## Tasks

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tasks/` | Auth | List tasks |
| `POST` | `/api/v1/tasks/` | Auth | Create task |
| `GET` | `/api/v1/tasks/{task_id}/` | Auth | Task detail |
| `PATCH` | `/api/v1/tasks/{task_id}/` | Auth | Update task |
| `DELETE` | `/api/v1/tasks/{task_id}/` | Auth | Delete task |

## Ads

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/ads/active/` | Public | Active ad feed |
| `GET` | `/api/v1/ads/active/{campaign_id}/click/` | Public | Record ad click |
| `GET` | `/api/v1/ads/campaigns/` | Auth | My ad campaigns |
| `POST` | `/api/v1/ads/campaigns/` | Auth | Create ad campaign |
| `GET` | `/api/v1/ads/campaigns/me/` | Auth | My campaigns alias |
| `GET` | `/api/v1/ads/campaigns/{campaign_id}/` | Auth | Campaign detail |
| `PATCH` | `/api/v1/ads/campaigns/{campaign_id}/` | Auth | Update campaign |
| `DELETE` | `/api/v1/ads/campaigns/{campaign_id}/` | Auth | Delete campaign |

## Store / Commerce

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/products/` | Public | Product list |
| `POST` | `/api/v1/products/` | Auth | Create product |
| `GET` | `/api/v1/products/{product_id}/` | Public | Product detail |
| `PATCH` | `/api/v1/products/{product_id}/` | Auth | Update product |
| `DELETE` | `/api/v1/products/{product_id}/` | Auth | Delete product |
| `GET` | `/api/v1/orders/` | Auth | Order list |
| `POST` | `/api/v1/orders/` | Auth | Create order |
| `GET` | `/api/v1/orders/{order_id}/` | Auth | Order detail |
| `PATCH` | `/api/v1/orders/{order_id}/` | Auth | Update order |
| `DELETE` | `/api/v1/orders/{order_id}/` | Auth | Delete order |
| `GET` | `/api/v1/cart/` | Auth | Cart |
| `POST` | `/api/v1/cart/` | Auth | Update cart |
| `GET` | `/api/v1/cart/items/` | Auth | Cart items |
| `POST` | `/api/v1/cart/items/` | Auth | Add cart item |
| `DELETE` | `/api/v1/cart/items/{product_id}/` | Auth | Remove cart item |
| `GET` | `/api/v1/store/products/` | Public | Store product alias |
| `POST` | `/api/v1/store/checkout/` | Auth | Checkout |
| `GET` | `/api/v1/store/orders/me/` | Auth | My store orders |

## Media

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/media/upload/` | Auth | Upload image or video |

## Search / Discovery

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/trending/topics/` | Public | Trending topics |
| `GET` | `/api/v1/search/users/` | Public | Search users |
| `GET` | `/api/v1/search/posts/` | Public | Search posts |
| `GET` | `/api/v1/search/` | Public | Unified search |

## Messaging

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/messages/conversations/` | Auth | Conversations list |
| `GET` | `/api/v1/messages/conversations/{user_id}/` | Auth | Conversation detail |
| `POST` | `/api/v1/messages/` | Auth | Create direct message |
| `PATCH` | `/api/v1/messages/{message_id}/read/` | Auth | Mark message read |
| `GET` | `/api/v1/messages/unread-count/` | Auth | Unread message count |

## AI / Utility

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/ai/posting-time-suggestions/` | Auth | Posting time suggestions |
| `GET` | `/api/v1/ai/content-insights/` | Auth | Content insights |

## Admin

All admin endpoints require staff/admin privileges.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/admin/me/role/` | Admin | Current admin role |
| `GET` | `/api/v1/admin/stats/` | Admin | Admin stats |
| `GET` | `/api/v1/admin/dashboard/stats/` | Admin | Dashboard stats alias |
| `GET` | `/api/v1/admin/users/` | Admin | Admin user list |
| `POST` | `/api/v1/admin/users/{user_id}/verify/` | Admin | Verify user |
| `POST` | `/api/v1/admin/users/{user_id}/ban/` | Admin | Ban user |
| `GET` | `/api/v1/admin/posts/` | Admin | Admin post list |
| `GET` | `/api/v1/admin/reports/` | Admin | Report list |
| `GET` | `/api/v1/admin/reports/{report_id}/` | Admin | Report detail |
| `PATCH` | `/api/v1/admin/reports/{report_id}/` | Admin | Update report |
| `GET` | `/api/v1/admin/ads/` | Admin | Admin ad campaigns |
| `GET` | `/api/v1/admin/ads/{campaign_id}/` | Admin | Admin ad detail |

## Notes

- This file documents the API surface currently mounted in the Django URL configuration.
- If a route appears in a router section and not in an explicit table, check the relevant ViewSet for permissions and serializer details.
- When backend routes change, update this file together with:
  - [core/urls.py](/C:/Users/somto/Projects/Herald_backend/core/urls.py)
  - [users/urls.py](/C:/Users/somto/Projects/Herald_backend/users/urls.py)
  - [core/api_root.py](/C:/Users/somto/Projects/Herald_backend/core/api_root.py)
