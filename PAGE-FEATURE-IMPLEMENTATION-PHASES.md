# Backend-Only Implementation Checklist (Full Route Coverage)

Use this as an execution checklist for backend delivery. Every route mounted in App routing is covered.

Base API target:
- https://herald-backend-6i3m.onrender.com/api/v1

## A. Global API Contract Checklist

- [ ] Accept Authorization: Bearer <token> on all protected endpoints.
- [ ] Return 401 with structured error payload for invalid or expired tokens.
- [ ] Support frontend trailing-slash usage on non-GET endpoints (or safe compatibility redirects).
- [ ] Standardize list responses to:
  {
    "data": [],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 0,
      "total_pages": 0
    }
  }
- [ ] Return timestamps as ISO UTC strings (example: 2026-03-18T10:00:00Z).
- [ ] Keep flattened post author fields in post payloads: username, display_name, avatar_url, is_verified (optional is_creator), plus author_id.
- [ ] Keep create-post idempotency guard (same user + identical content within short time window).

## B. Route Checklist (All Mounted Pages)

## 1) / (Index)
- [ ] GET /posts/?page=&limit=&sort=-created_at (public or auth-optional feed).
- [ ] GET /trending/topics/?limit=.
- [ ] GET /users/suggestions/?limit=.
- [ ] Realtime new-post stream support (websocket/SSE) for feed refresh parity.

## 2) /auth (Auth)
- [ ] POST /auth/signup/.
- [ ] POST /auth/signin/.
- [ ] POST /auth/signout/.
- [ ] POST /auth/refresh/.
- [ ] GET /users/me/.
- [ ] Optional warmup endpoint: GET /health/.

## 3) /feed (Feed)
- [ ] GET /posts/?page=&limit=&sort=.
- [ ] POST /posts/.
- [ ] DELETE /posts/{post_id}/.
- [ ] POST /posts/{post_id}/like/.
- [ ] DELETE /posts/{post_id}/like/.
- [ ] POST /posts/{post_id}/share/.
- [ ] POST /posts/{post_id}/bookmark/.
- [ ] GET /users/me/.
- [ ] GET /wallets/me/.
- [ ] GET /users/me/tasks/?completed=.
- [ ] POST /users/me/tasks/{task_id}/claim/.
- [ ] GET /posts/{post_id}/comments/?page=&limit=.
- [ ] POST /posts/{post_id}/comments/.
- [ ] DELETE /comments/{comment_id}/.
- [ ] POST /comments/{comment_id}/like/.
- [ ] Realtime: posts + comments events.

## 4) /dashboard (Dashboard)
- [ ] GET /users/me/.
- [ ] GET /wallets/me/.
- [ ] GET /users/me/posts/?page=&limit=&sort=.
- [ ] GET /users/me/earnings/?page=&limit=&from=&to=.
- [ ] GET /users/me/analytics/engagement-series?range=7d|30d (recommended).
- [ ] GET /users/me/analytics/audience-breakdown (recommended).

## 5) /explore (Explore)
- [ ] GET /posts/?sort=-likes_count&limit= (trending).
- [ ] GET /posts/?media_type=reel&sort=-created_at&limit= (reels).
- [ ] GET /users/?sort=-reputation&limit=.
- [ ] GET /wallets/me/ (when authenticated).

## 6) /wallet (Wallet)
- [ ] GET /wallets/me/.
- [ ] GET /wallets/me/transactions/?page=&limit=&type=.
- [ ] POST /wallets/me/convert/ body { amount }.
- [ ] POST /wallets/transfer/ body { recipient_id, amount, currency }.
- [ ] Username lookup for transfer UX:
  - [ ] GET /users/by-username/{username} OR
  - [ ] GET /users/search?username=.

## 7) /profile (Profile)
- [ ] GET /users/me/.
- [ ] PATCH /users/me/.
- [ ] POST /users/me/avatar/ multipart upload.
- [ ] GET /users/me/posts/?page=&limit=&sort=.
- [ ] GET /wallets/me/.

## 8) /settings (Settings)
- [ ] GET /users/me/settings/.
- [ ] PATCH /users/me/settings/.
- [ ] POST /auth/change-password/.
- [ ] DELETE /users/me/ (account deletion flow).

## 9) /leaderboard (Leaderboard)
- [ ] GET /leaderboard/reputation/?limit=.
- [ ] GET /leaderboard/engagement/?limit=.
- [ ] GET /leaderboard/points/?limit=.
- [ ] GET /leaderboard/me/.
- [ ] Ensure response entries include: user_id, display_name, username, avatar_url, tier, reputation, is_verified, total_engagement, httn_points.

## 10) /notifications (Notifications)
- [ ] GET /notifications/?page=&limit=&read=.
- [ ] PATCH /notifications/{id}/ (mark read).
- [ ] POST /notifications/mark-all-read/.
- [ ] DELETE /notifications/{id}/.
- [ ] DELETE /notifications/clear-all/.
- [ ] Realtime notification stream (new + read-state updates + unread count updates).

## 11) /ads (Ads)
- [ ] GET /ads/campaigns/me/?page=&limit=&status=.
- [ ] POST /ads/campaigns/.
- [ ] PATCH /ads/campaigns/{id}/ (active/paused).
- [ ] DELETE /ads/campaigns/{id}/.
- [ ] GET /wallets/me/.
- [ ] Campaign fields: title, description, budget_points, spent_points, impressions, clicks, status, start_date, end_date, created_at.

## 12) /admin (Admin)
- [ ] GET /admin/me/role/ (or include role in /users/me/).
- [ ] GET /admin/dashboard/stats/.
- [ ] GET /admin/users/?page=&limit=&search=.
- [ ] GET /admin/posts/?page=&limit=&search=.
- [ ] GET /admin/reports/?page=&limit=&status=.
- [ ] POST /admin/users/{user_id}/verify/.
- [ ] Moderation endpoints (recommended): ban/unban user, hide/unhide post.

## 13) /user/:username (UserProfile)
- [ ] GET /users/by-username/{username}.
- [ ] GET /users/{id}/posts/?page=&limit=&sort=.
- [ ] GET /users/{id}/stats/.

## 14) /store (EStore)
- [ ] GET /store/products/?page=&limit=&category=&search=.
- [ ] GET /wallets/me/.
- [ ] POST /store/checkout/ (atomic: validate funds, debit wallet, create order, create transactions).
- [ ] GET /store/orders/me/?page=&limit=.

## 15) /live (Live)
- [ ] GET /streams/?status=live|scheduled|ended&page=&limit=&sort=.
- [ ] GET /streams/{id}/.
- [ ] POST /streams/ (start/schedule).
- [ ] PATCH /streams/{id}/ (status updates).
- [ ] Include host profile data in stream payload (or a resolved join payload).

## 16) /communities (Communities)
- [ ] GET /communities/?page=&limit=&sort=&category=.
- [ ] GET /users/me/communities/.
- [ ] POST /communities/.
- [ ] POST /communities/{id}/join/.
- [ ] DELETE /communities/{id}/join/.
- [ ] Community fields: id, name, description, category, image_url, member_count, is_private, created_by.

## 17) /causes (Causes)
- [ ] GET /causes/?page=&limit=&sort=&category=.
- [ ] GET /causes/{id}/.
- [ ] POST /causes/{id}/donate/ body { amount, payment_type, message? }.
- [ ] GET /wallets/me/.
- [ ] Cause fields: id, title, description, category, goal_amount, raised_amount, status, image_url, created_by.

## 18) /news (News)
- [ ] GET /news/?page=&limit=&category=&source=&sort=.
- [ ] GET /news/{id}/.
- [ ] POST /news/{id}/like/.
- [ ] POST /news/{id}/bookmark/.
- [ ] Optional: DELETE /news/{id}/bookmark/.
- [ ] Article fields: id, title, summary, content, source, source_type, image_url, external_url, published_at.

## 19) /db-test (DbTest)
- [ ] Decide route strategy:
  - [ ] Remove from production routing OR
  - [ ] Replace with backend diagnostics.
- [ ] If retained, provide:
  - [ ] GET /health/
  - [ ] GET /health/db/
  - [ ] GET /health/auth/

## 20) * (NotFound)
- [x] No backend work required.

## C. Shared Backend Services Checklist (Cross-Page)

## Messaging service (MessagesPopup, FloatingMessageButton, MobileBottomNav)
- [ ] GET /messages/conversations/.
- [ ] GET /messages/conversations/{user_id}/.
- [ ] POST /messages/.
- [ ] PATCH /messages/{id}/read/.
- [ ] GET /messages/unread-count/.
- [ ] GET /users/search?query= for new conversation target.
- [ ] Realtime channel for new messages + unread counters.

## Follow graph (FollowButton)
- [ ] GET /follows/status/{target_user_id}/.
- [ ] POST /follows/{target_user_id}/.
- [ ] DELETE /follows/{target_user_id}/.
- [ ] Atomic follower/following counter updates.
- [ ] Follow notification trigger.

## Onboarding service (OnboardingFlow)
- [ ] GET /users/suggested/?limit=.
- [ ] PATCH /users/me/ (account type).
- [ ] PUT /users/me/interests/.
- [ ] POST /users/me/follows/bulk/.
- [ ] POST /users/me/onboarding/complete/.

## Media upload (MediaUpload)
- [ ] POST /media/upload/ multipart.
- [ ] Return durable URL + media metadata.

## Scheduled posting (SchedulePostDialog)
- [ ] POST /posts/scheduled/.
- [ ] GET /posts/scheduled/me/.
- [ ] POST /ai/posting-time-suggestions/.

## Live internals (LiveStreamViewer)
- [ ] GET /streams/{id}/chat?limit=.
- [ ] POST /streams/{id}/chat/.
- [ ] GET /streams/{id}/donations?limit=.
- [ ] POST /streams/{id}/donations/.
- [ ] POST /streams/{id}/viewer-join/.
- [ ] POST /streams/{id}/viewer-leave/.
- [ ] Realtime channels/events for chat, donations, and viewer count.
- [ ] Wallet debit/credit handled transaction-safely on donation.

## Search (SearchBar)
- [ ] GET /search/users?q=.
- [ ] GET /search/posts?q=.

## AI insights (ContentInsights)
- [ ] POST /ai/content-insights/.

## D. Compatibility Alias Checklist (Temporary)

- [ ] Keep /auth/users/profiles/me/ -> /users/me/ compatibility during migration.
- [ ] Keep /auth/users/profiles/me/tasks/ -> /users/me/tasks/ compatibility during migration.
- [ ] Keep /auth/users/profiles/me/tasks/{id}/claim/ -> /users/me/tasks/{id}/claim/ compatibility during migration.

## E. Backend Sign-Off Checklist

- [ ] All 20 mounted routes verified against required endpoints.
- [ ] No production page depends on direct Supabase tables/functions.
- [ ] Realtime channels defined for notifications/messages/live where required.
- [ ] Endpoint auth and error payloads conform to global contract.
- [ ] Pagination shape is consistent across list endpoints.
- [ ] Smoke test pass: auth -> feed -> create post -> interact -> wallet -> notifications -> logout.
