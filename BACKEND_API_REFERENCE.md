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

## Explore

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/explore/for_you/` | Public | Explore For You guide |
| `GET` | `/api/v1/explore/trending/` | Public | Explore Trending guide |
| `GET` | `/api/v1/explore/news/` | Public | Explore News guide |
| `GET` | `/api/v1/explore/sports/` | Public | Explore Sports guide |
| `GET` | `/api/v1/explore/entertainment/` | Public | Explore Entertainment guide |

### Explore tab structure

Herald's Explore guide follows the same high-level shape X describes in its official Explore documentation:

- `For You`: a personalized mix of recommended trends and posts
- `Trending`: non-personalized trending topics
- `News`, `Sports`, `Entertainment`: category-filtered story clusters

`GET /api/v1/explore/for_you/`

- Returns a backend-mixed guide of `topic` and `post` items
- Uses Herald's feed ranker plus user-interest overlap to order items

Example response:

```json
{
  "tab": "for_you",
  "items": [
    {
      "id": "topic-ai-0",
      "type": "topic",
      "topic": {
        "name": "#ai",
        "topic": "ai",
        "tag": "#ai",
        "posts_count": 122
      }
    },
    {
      "id": "post-uuid",
      "type": "post",
      "post": {
        "id": "uuid",
        "content": "post text"
      }
    }
  ],
  "topics": [],
  "posts": []
}
```

`GET /api/v1/explore/trending/`

- Returns trending topics only
- Intended for the Explore `Trending` tab

`GET /api/v1/explore/news/`
`GET /api/v1/explore/sports/`
`GET /api/v1/explore/entertainment/`

- Return server-classified news clusters for each section
- The category decision is made on the backend from article metadata and content signals, not in the mobile client

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
| `GET` | `/api/v1/posts/feed/` | Public | **Algorithmic For You feed** (see below) |
| `GET` | `/api/v1/posts/` | Public | Global post list (chronological / sorted) |
| `POST` | `/api/v1/posts/` | Auth | Create post |
| `GET` | `/api/v1/posts/{post_id}/` | Public | Post detail |
| `PATCH` | `/api/v1/posts/{post_id}/` | Auth | Update post |
| `DELETE` | `/api/v1/posts/{post_id}/` | Auth | Delete post |
| `GET` | `/api/v1/posts/trending/` | Public | Trending posts (48 h engagement window) |
| `GET` | `/api/v1/posts/following/` | Auth | Chronological feed of followed accounts |
| `POST` | `/api/v1/posts/{post_id}/like/` | Auth | Like post |
| `DELETE` | `/api/v1/posts/{post_id}/like/` | Auth | Unlike |
| `POST` | `/api/v1/posts/{post_id}/unlike/` | Auth | Unlike alias |
| `POST` | `/api/v1/posts/{post_id}/share/` | Auth | Repost / share |
| `POST` | `/api/v1/posts/{post_id}/bookmark/` | Auth | Bookmark post |
| `POST` | `/api/v1/posts/{post_id}/unbookmark/` | Auth | Remove bookmark |
| `GET` | `/api/v1/posts/{post_id}/comments/` | Public | List post comments |
| `POST` | `/api/v1/posts/{post_id}/comments/` | Auth | Create comment / reply |
| `POST` | `/api/v1/posts/scheduled/` | Auth | Create scheduled post |
| `GET` | `/api/v1/posts/scheduled/me/` | Auth | My scheduled posts |

---

### GET `/api/v1/posts/feed/` — Algorithmic For You Feed

The primary feed endpoint for the app's **For You** tab. Returns a personalised ranked blend of in-network and out-of-network posts, similar to X's For You algorithm.

**Authentication:** Optional — authenticated users get personalised results, anonymous users get global ranking.

**Query parameters**

| Param | Type | Default | Description |
| --- | --- | --- | --- |
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Results per page (max 50) |

**Response `200`**

```json
{
  "data": [
    {
      "id": "uuid",
      "content": "post text",
      "media_url": "https://...",
      "media_urls": [],
      "media_type": "image",
      "likes_count": 14,
      "comments_count": 3,
      "shares_count": 2,
      "bookmarks_count": 1,
      "views_count": 120,
      "httn_earned": 25,
      "is_liked": false,
      "is_reposted": false,
      "is_bookmarked": false,
      "created_at": "2025-01-01T00:00:00Z",
      "author": {
        "id": "uuid",
        "username": "joel",
        "display_name": "Joel",
        "avatar_url": "https://...",
        "is_verified": false,
        "is_creator": false,
        "tier": null
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "has_more": true,
    "total": 420,
    "total_pages": 21
  }
}
```

**Ranking algorithm**

Each post receives a score combining:

| Signal | Weight | Notes |
| --- | --- | --- |
| Freshness | up to +42 | Decays over 96 hours |
| Engagement velocity | ×3.8 | `(likes + comments×2.2 + shares×3.4 + bookmarks×2.8) / age^0.72` |
| Followed author | +34 | Direct follow of the post's author |
| Previously engaged author | +18 | You liked/reposted/bookmarked this author before |
| Liked by someone you follow | +14 | Social proof from your network |
| Second-degree follow | up to +14 | Mutual connections vouch for the author |
| Interest / topic match | +8.5 per overlap | Based on your interests and past engagement |
| Hashtag match | +5 per overlap | Hashtags in post vs. your interest terms |
| Verified badge | +4 | |
| Creator status | +3.5 | |
| Premium tier | +1.5 | |
| Author reputation | up to +7 | `reputation / 80`, capped |
| Has media | +2.5 | Images or video |
| Author is live | +12 | Currently streaming |

**Blend strategy (authenticated users with follows)**

- ~40% **in-network**: recent posts from accounts you follow, scored and ranked
- ~60% **out-of-network**: posts from accounts you don't follow, scored and ranked
- A diversity pass prevents the same author appearing more than twice in any 5-post window

**Caching**

Responses are cached per user per page for **30 seconds**. Cache is invalidated on any post create, delete, like, or repost event (`bump_post_timeline_cache_version()`).

**`GET /api/v1/posts/following/` — Following Tab**

Chronological feed of posts exclusively from accounts the authenticated user follows. No ranking applied — newest first. Uses the same `has_more` pagination pattern.

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

### News filtering

`GET /api/v1/news/` supports `section=` with:

- `news`
- `sports`
- `entertainment`

News article payloads now include a stored server-owned `section` field so Explore, article detail, and any future clients can use the same categorization contract.

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
| `GET` | `/api/v1/communities/feed/` | Auth | Home feed of posts from joined communities |
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

## Marketplace

The Marketplace lets users browse, list, and purchase digital and physical products. Prices are denominated in **Espees** (the platform currency, stored as `espees` on the wallet). The `price` field is always a decimal string in API responses.

### Currency

All prices are in Espees. The app displays the unit as `HTTN`. The wallet field is `wallet.espees`. Purchases deduct directly from the buyer's wallet balance.

### Categories

Valid `category` values: `nfts`, `tools`, `subscriptions`, `merchandise`, `digital`, `courses`, `general`.

---

### GET `/api/v1/store/products/`

Browse marketplace listings. No authentication required.

**Query parameters**

| Param | Type | Description |
| --- | --- | --- |
| `category` | string | Filter by category (see Categories above) |
| `search` | string | Full-text search on `name` and `description` |

**Response `200`**

```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Herald Premium Monthly",
      "description": "Unlock verified badge eligibility, unlimited scheduling...",
      "category": "subscriptions",
      "price": "500.00",
      "image_url": "https://...",
      "seller": "username_or_null",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

Returns up to 60 products ordered by newest first. No pagination cursor — pull-to-refresh to get new listings.

---

### POST `/api/v1/store/products/`

List a product on the marketplace. Requires authentication.

**Request body**

```json
{
  "name": "My Digital Asset",
  "description": "Optional description",
  "price": 250,
  "category": "digital",
  "image_url": "https://..."
}
```

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | Yes | Max 200 chars |
| `description` | string | No | |
| `price` | number | Yes | Decimal ≥ 0. `0` = free |
| `category` | string | No | Defaults to `general` |
| `image_url` | string | No | Must be a valid URL |

**Response `201`**

Same shape as a single product object from the list response, with `seller` set to the authenticated user's username.

**Errors**

| Status | Condition |
| --- | --- |
| `400` | Missing `name` or invalid `price` |
| `404` | Authenticated user has no profile |

---

### POST `/api/v1/store/checkout/`

Purchase one or more products using the buyer's Espees wallet. Requires authentication.

**Request body**

```json
{
  "items": [
    { "product_id": "uuid", "quantity": 1 }
  ],
  "total_amount": 500,
  "payment_type": "wallet"
}
```

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `items` | array | Yes | At least one item |
| `total_amount` | number | Yes | Must be > 0 |
| `payment_type` | string | Yes | Only `wallet` is supported |

**Response `201`**

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "items": [{ "product_id": "uuid", "quantity": 1 }],
  "total_amount": "500.00",
  "payment_type": "wallet",
  "status": "completed",
  "created_at": "2025-01-01T00:00:00Z",
  "completed_at": "2025-01-01T00:00:00Z"
}
```

`status` is `completed` when the wallet deduction succeeds. A `Transaction` record is also created with `transaction_type: "purchase"`.

**Errors**

| Status | Condition |
| --- | --- |
| `400` | Missing `items`, invalid `total_amount`, or insufficient Espees balance |
| `404` | User profile or wallet not found |

---

### GET `/api/v1/store/orders/me/`

Retrieve the authenticated user's purchase history. Requires authentication.

**Response `200`**

```json
{
  "data": [
    {
      "id": "uuid",
      "items": [{ "product_id": "uuid", "quantity": 1 }],
      "total_amount": "500.00",
      "payment_type": "wallet",
      "status": "completed",
      "created_at": "2025-01-01T00:00:00Z",
      "completed_at": "2025-01-01T00:00:00Z"
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total": 5, "total_pages": 1 }
}
```

Order statuses: `pending`, `completed`, `cancelled`.

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
