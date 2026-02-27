# Herald Social - Django Backend API Requirements

**Target Audience**: Django backend developers building REST APIs  
**Database Schema**: PostgreSQL (based on Supabase schema)  
**Framework Recommendation**: Django REST Framework with Token Authentication
          user_id = ForeignKey(User, on_delete=models.CASCADE)

---

## Table of Contents
1. [Authentication](#authentication)
2. [Core Data Models](#core-data-models)
3. [API Endpoints by Page](#api-endpoints-by-page)
4. [Database Schema](#database-schema)
5. [Authentication Flow](#authentication-flow)

---


## Authentication

### Auth Model (JWT-based)
- **Provider**: Django authentication with JWT tokens
- **Storage**: Client stores token in localStorage
- **Token Refresh**: Automatic token refresh on each request

### Required Auth Endpoints

```
POST   /api/v1/auth/signup
POST   /api/v1/auth/signin
POST   /api/v1/auth/signout
POST   /api/v1/auth/refresh
GET    /api/v1/auth/user (current user)
GET    /api/v1/auth/session
```

### Signup Payload
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "username": "johndoe"
}
```

### Response
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "user_id": "uuid"
  },
  "session": {
    "access_token": "jwt_token",
    "token_type": "Bearer",
    "expires_in": 3600
  }
---

## Core Data Models

### 1. Users (User Profiles)
```python
class User(models.Model):
    id = UUIDField(primary_key=True)
    user_id = ForeignKey(auth.User)  # Link to auth.users
    username = CharField(unique=True, max_length=100)
    display_name = CharField(max_length=200)
    full_name = CharField(max_length=200, null=True)
    email = EmailField()
    avatar_url = URLField(null=True)
    bio = TextField(null=True)
    tier = CharField(choices=['free', 'creator', 'premium'], default='free')
    reputation = IntegerField(default=0)
    is_verified = BooleanField(default=False)
    is_creator = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### 2. Posts
```python
class Post(models.Model):
    id = UUIDField(primary_key=True)
    author_id = ForeignKey(User, to_field='user_id')
    content = TextField()
    media_url = URLField(null=True)
    media_type = CharField(choices=['image', 'video', 'reel'], null=True)
    likes_count = IntegerField(default=0)
    comments_count = IntegerField(default=0)
    shares_count = IntegerField(default=0)
    httn_earned = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### 3. Wallets
```python
class Wallet(models.Model):
    id = UUIDField(primary_key=True)
    user_id = ForeignKey(User, unique=True)
    httn_points = IntegerField(default=0)
    httn_tokens = DecimalField()
    espees = DecimalField()
    pending_rewards = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### 4. Communities
```python
class Community(models.Model):
    id = UUIDField(primary_key=True)
    name = CharField(max_length=200)
    description = TextField(null=True)
    category = CharField(max_length=50)
    created_by = ForeignKey(User)
    image_url = URLField(null=True)
    is_private = BooleanField(default=False)
    member_count = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### 5. Comments
```python
class Comment(models.Model):
    id = UUIDField(primary_key=True)
    post_id = ForeignKey(Post)
    author_id = ForeignKey(User)
    content = TextField()
    likes_count = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### 6. Post Interactions (Likes, Reposts, Bookmarks)
```python
class PostInteraction(models.Model):
    id = UUIDField(primary_key=True)
    post_id = ForeignKey(Post)
    user_id = ForeignKey(User)
    interaction_type = CharField(choices=['like', 'share', 'bookmark'])
    created_at = DateTimeField(auto_now_add=True)
```

### 7. Wallets
```python
class WalletBalance(models.Model):
    user_id = ForeignKey(User, unique=True)
    httn_points = IntegerField()
    httn_tokens = DecimalField()
    espees = DecimalField()
    pending_rewards = IntegerField()
```

### 8. Notifications
```python
class Notification(models.Model):
    id = UUIDField(primary_key=True)
    user_id = ForeignKey(User)
    notification_type = CharField(choices=['like', 'comment', 'follow', 'share'])
    title = CharField(max_length=200)
    message = TextField()
    related_resource_type = CharField(max_length=50)
    related_resource_id = CharField(max_length=100)
    read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

### 9. Tasks/Gamification
```python
class UserTask(models.Model):
    id = UUIDField(primary_key=True)
    user_id = ForeignKey(User)
    title = CharField(max_length=200)
    description = TextField(null=True)
    task_type = CharField(choices=['daily', 'weekly', 'campaign'])
    reward = IntegerField()  # Points
    progress = IntegerField(default=0)
    target = IntegerField()
    completed = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

### 10. Causes (Fundraisers)
```python
class Cause(models.Model):
    id = UUIDField(primary_key=True)
    title = CharField(max_length=200)
    description = TextField()
    category = CharField(max_length=50)
    created_by = ForeignKey(User)
    goal_amount = DecimalField()
    raised_amount = DecimalField(default=0)
    image_url = URLField(null=True)
    status = CharField(choices=['active', 'completed', 'cancelled'])
    created_at = DateTimeField(auto_now_add=True)
    end_date = DateField(null=True)
```

### 11. Live Streams
```python
class LiveStream(models.Model):
    id = UUIDField(primary_key=True)
    user_id = ForeignKey(User)
    title = CharField(max_length=200)
    description = TextField(null=True)
    status = CharField(choices=['scheduled', 'live', 'ended'])
    stream_url = URLField(null=True)
    thumbnail_url = URLField(null=True)
    viewer_count = IntegerField(default=0)
    started_at = DateTimeField(null=True)
    ended_at = DateTimeField(null=True)
    scheduled_for = DateTimeField(null=True)
    created_at = DateTimeField(auto_now_add=True)
```

### 12. News
```python
class NewsArticle(models.Model):
    id = UUIDField(primary_key=True)
    title = CharField(max_length=300)
    content = TextField()
    category = CharField(max_length=50)
    source_url = URLField(null=True)
    image_url = URLField(null=True)
    likes_count = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
```

### 13. Ad Campaigns
```python
class AdCampaign(models.Model):
    id = UUIDField(primary_key=True)
    user_id = ForeignKey(User)
    title = CharField(max_length=200)
    description = TextField(null=True)
    budget_points = IntegerField()
    spent_points = IntegerField(default=0)
    impressions = IntegerField(default=0)
    clicks = IntegerField(default=0)
    status = CharField(choices=['active', 'paused', 'completed'])
    target_audience = JSONField(null=True)
    start_date = DateField(null=True)
    end_date = DateField(null=True)
    created_at = DateTimeField(auto_now_add=True)
```

### 14. Orders (E-commerce)
```python
class Order(models.Model):
    id = UUIDField(primary_key=True)
    user_id = ForeignKey(User)
    items = JSONField()  # [{product_id, quantity, price}]
    total_amount = DecimalField()
    payment_type = CharField(choices=['card', 'wallet', 'crypto'])
    status = CharField(choices=['pending', 'completed', 'cancelled'])
    created_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True)
```

---

## API Endpoints by Page

### 1. **Feed Page** (`/feed`)

#### Get User Data
```
GET  /api/v1/users/<user_id>/
     Response: User profile + wallet + tasks
```

#### Get Posts (with pagination)
```
GET  /api/v1/posts/?page=1&limit=20
     Response: [
       {
         "id": "uuid",
         "author": {User object},
         "content": "text",
         "media_url": "url",
         "likes_count": 10,
         "comments_count": 2,
         "shares_count": 1,
         "httn_earned": 25,
         "created_at": "2026-02-23T10:00:00Z"
       }
     ]
```

#### Get Top Creators
```
GET  /api/v1/users/?sort=-reputation&limit=5
     Response: [User objects sorted by reputation]
```

#### Create Post
```
POST /api/v1/posts/
     {
       "content": "text",
       "media_url": "url (optional)",
       "media_type": "image|video|reel"
     }
     Response: Created Post object
```

#### Like Post
```
POST /api/v1/posts/<post_id>/like/
     Response: {success: true, likes_count: new_count}
```

#### Unlike Post
```
DELETE /api/v1/posts/<post_id>/like/
       Response: {success: true, likes_count: new_count}
```

#### Repost
```
POST /api/v1/posts/<post_id>/share/
     Response: {success: true, shares_count: new_count}
```

#### Bookmark Post
```
POST /api/v1/posts/<post_id>/bookmark/
     Response: {success: true}
```

#### Delete Post
```
DELETE /api/v1/posts/<post_id>/
       Response: {success: true}
```

#### Get Wallet Balance
```
GET  /api/v1/wallets/<user_id>/
     Response: {
       "httn_points": 1000,
       "httn_tokens": 50.25,
       "espees": 100.00,
       "pending_rewards": 500
     }
```

#### Get User Tasks
```
GET  /api/v1/users/<user_id>/tasks/?completed=false
     Response: [UserTask objects]
```

#### Claim Task Reward
```
POST /api/v1/users/<user_id>/tasks/<task_id>/claim/
     Response: {success: true, reward: 100}
```

---

### 2. **Explore Page** (`/explore`)

#### Get Trending Posts
```
GET  /api/v1/posts/?sort=-likes_count&limit=10
     Response: [Posts ordered by likes]
```

#### Get All Users (for trending)
```
GET  /api/v1/users/?sort=-reputation&limit=10
     Response: [Top users by reputation]
```

#### Get Reel Videos
```
GET  /api/v1/posts/?media_type=reel&sort=-created_at&limit=12
     Response: [Reel posts]
```

#### Get User Wallet (for current user)
```
GET  /api/v1/wallets/<user_id>/
     Response: Wallet object
```

---

### 3. **Profile Page** (`/profile`)

#### Get Current User Profile
```
GET  /api/v1/users/me/
     Response: Current User object (authenticated)
```

#### Update User Profile
```
PATCH /api/v1/users/me/
      {
        "display_name": "John Doe",
        "bio": "Software engineer",
        "avatar_url": "https://...",
        "location": "San Francisco"
      }
      Response: Updated User object
```

#### Get User Posts
```
GET  /api/v1/users/me/posts/?page=1&limit=20
     Response: [Posts by current user]
```

#### Get User Stats
```
GET  /api/v1/users/me/stats/
     Response: {
       "posts_count": 42,
       "followers_count": 1500,
       "following_count": 300,
       "reputation": 8500
     }
```

#### Follow User
```
POST /api/v1/users/<user_id>/follow/
     Response: {success: true, followers_count: new_count}
```

#### Unfollow User
```
DELETE /api/v1/users/<user_id>/follow/
       Response: {success: true, followers_count: new_count}
```

#### Get User's Wallet
```
GET  /api/v1/wallets/me/
     Response: Wallet object
```

#### Update User Settings
```
PATCH /api/v1/users/me/settings/
      {
        "notifications_enabled": true,
        "privacy_level": "public|private|friends_only",
        "email_updates": true
      }
      Response: Updated settings
```

---

### 4. **User Profile Page** (`/profile/:username`)

#### Get User by Username
```
GET  /api/v1/users/by-username/<username>/
     Response: User object
```

#### Get User's Posts
```
GET  /api/v1/users/<user_id>/posts/?page=1&limit=20
     Response: [Posts by specified user]
```

#### Get Follower/Following Lists
```
GET  /api/v1/users/<user_id>/followers/?page=1&limit=20
GET  /api/v1/users/<user_id>/following/?page=1&limit=20
     Response: [User objects]
```

---

### 5. **Communities Page** (`/communities`)

#### Get All Communities
```
GET  /api/v1/communities/?page=1&limit=20&sort=-member_count
     Response: [Community objects]
```

#### Create Community
```
POST /api/v1/communities/
     {
       "name": "Tech Lovers",
       "description": "Community for tech enthusiasts",
       "category": "technology",
       "is_private": false,
       "image_url": "https://..."
     }
     Response: Created Community object
```

#### Get Community Details
```
GET  /api/v1/communities/<community_id>/
     Response: Community object with members list
```

#### Join Community
```
POST /api/v1/communities/<community_id>/join/
     Response: {success: true, member_count: new_count}
```

#### Leave Community
```
DELETE /api/v1/communities/<community_id>/join/
       Response: {success: true, member_count: new_count}
```

#### Get Community Posts
```
GET  /api/v1/communities/<community_id>/posts/?page=1&limit=20
     Response: [Posts in community]
```

#### Create Community Post
```
POST /api/v1/communities/<community_id>/posts/
     {
       "content": "text",
       "media_url": "url (optional)"
     }
     Response: Created Post object
```

---

### 6. **Causes/Fundraisers Page** (`/causes`)

#### Get All Causes
```
GET  /api/v1/causes/?page=1&limit=20&sort=-raised_amount
     Response: [Cause objects]
```

#### Create Cause
```
POST /api/v1/causes/
     {
       "title": "Help Build Schools",
       "description": "Fundraiser for education",
       "category": "education",
       "goal_amount": 50000.00,
       "image_url": "https://...",
       "end_date": "2026-12-31"
     }
     Response: Created Cause object
```

#### Get Cause Details
```
GET  /api/v1/causes/<cause_id>/
     Response: Cause object with donation history
```

#### Donate to Cause
```
POST /api/v1/causes/<cause_id>/donate/
     {
       "amount": 100.00,
       "payment_type": "wallet|card|crypto"
     }
     Response: {success: true, new_raised_amount: 50100}
```

---

### 7. **Live Page** (`/live`)

#### Get Active Live Streams
```
GET  /api/v1/streams/?status=live&sort=-viewer_count
     Response: [LiveStream objects]
```

#### Get Scheduled Streams
```
GET  /api/v1/streams/?status=scheduled&sort=scheduled_for
     Response: [Scheduled streams]
```

#### Start Live Stream
```
POST /api/v1/streams/
     {
       "title": "Live Coding Session",
       "description": "Building a web app",
       "stream_url": "rtmp://..."
     }
     Response: Created LiveStream object with stream_url
```

#### Update Stream Stats
```
PATCH /api/v1/streams/<stream_id>/
      {
        "viewer_count": 150,
        "status": "live"
      }
      Response: Updated LiveStream object
```

#### End Live Stream
```
PATCH /api/v1/streams/<stream_id>/
      {"status": "ended"}
      Response: Ended stream object
```

---

### 8. **News Page** (`/news`)

#### Get News Articles
```
GET  /api/v1/news/?page=1&limit=20&category=tech&sort=-created_at
     Response: [NewsArticle objects]
```

#### Get News by Category
```
GET  /api/v1/news/?category=religion|health|tech&limit=20
     Response: [News articles]
```

#### Like Article
```
POST /api/v1/news/<article_id>/like/
     Response: {success: true, likes_count: new_count}
```

#### Bookmark Article
```
POST /api/v1/news/<article_id>/bookmark/
     Response: {success: true}
```

---

### 9. **E-Store Page** (`/estore`)

#### Get Products
```
GET  /api/v1/products/?page=1&limit=20&category=merch&sort=-created_at
     Response: [Product objects]
```
GET  /api/v1/cart/
     Response: {items: [...], total_amount: 100.00}
```

#### Add to Cart
```
POST /api/v1/cart/items/
     {
       "product_id": "uuid",
       "quantity": 2
     }
     Response: Updated cart object
```

#### Remove from Cart
```
DELETE /api/v1/cart/items/<product_id>/
       Response: Updated cart object
```

#### Checkout
```
POST /api/v1/orders/
     {
       "items": [{product_id, quantity}],
       "total_amount": 100.00,
       "payment_type": "wallet|card|crypto"
     }
     Response: Created Order object
```

---

### 10. **Wallet Page** (`/wallet`)

#### Get Wallet Balance
```
GET  /api/v1/wallets/me/
     Response: {
       "httn_points": 1000,
       "httn_tokens": 50.25,
       "espees": 100.00,
       "pending_rewards": 500,
       "transactions": [...]
     }
```

#### Get Transaction History
```
GET  /api/v1/wallets/me/transactions/?page=1&limit=50
     Response: [Transaction objects]
```

#### Convert Points to Tokens
```
POST /api/v1/wallets/me/convert/
     {
       "from_currency": "points",
       "to_currency": "tokens",
       "amount": 500
     }
     Response: {success: true, new_balance: {...}}
```

#### Withdraw
```
POST /api/v1/wallets/me/withdraw/
     {
       "amount": 50.00,
       "payment_method": "bank|crypto"
     }
     Response: {success: true, transaction_id: "uuid"}
```

---

### 11. **Notifications Page** (`/notifications`)

#### Get Notifications
```
GET  /api/v1/notifications/?page=1&limit=50&read=false
     Response: [Notification objects]
```

#### Mark Notification as Read
```
PATCH /api/v1/notifications/<notification_id>/
      {"read": true}
      Response: Updated Notification object
```

#### Mark All as Read
```
POST /api/v1/notifications/mark-all-read/
     Response: {success: true}
```

#### Delete Notification
```
DELETE /api/v1/notifications/<notification_id>/
       Response: {success: true}
```

---

### 12. **Leaderboard Page** (`/leaderboard`)

#### Get Top Users by Reputation
```
GET  /api/v1/leaderboard/?sort=-reputation&limit=100&page=1
     Response: [User objects with rank]
```

#### Get Top Users by Activity
```
GET  /api/v1/leaderboard/activity/?limit=100&period=week|month|all_time
     Response: [Users with activity stats]
```

#### Get Current User's Rank
```
GET  /api/v1/leaderboard/me/
     Response: {
       "rank": 15,
       "reputation": 8500,
       "percentile": 92
     }
```

---

### 13. **Admin Dashboard** (`/admin`)

#### Get Dashboard Stats
```
GET  /api/v1/admin/stats/
     Response: {
       "total_users": 10000,
       "total_posts": 50000,
       "total_revenue": 100000.00,
       "active_users_today": 2000
     }
```

#### Get All Users (Admin)
```
GET  /api/v1/admin/users/?page=1&limit=50&sort=-created_at
     Response: [User objects]
```

#### Get All Posts (Admin)
```
GET  /api/v1/admin/posts/?page=1&limit=50&flagged=false
     Response: [Post objects]
```

#### Flag/Report Content
```
POST /api/v1/admin/reports/
     {
       "resource_type": "post|comment|user",
       "resource_id": "uuid",
       "reason": "inappropriate",
       "description": "details"
     }
     Response: Created Report object
```

#### Ban User (Admin)
```
POST /api/v1/admin/users/<user_id>/ban/
     {
       "reason": "content policy violation",
       "duration_days": 30
     }
     Response: {success: true, banned_until: "2026-03-26"}
```

#### Approve Post (Admin)
```
PATCH /api/v1/admin/posts/<post_id>/
      {"status": "approved"}
      Response: Updated Post object
```

---

### 14. **Settings Page** (`/settings`)

#### Get User Settings
```
GET  /api/v1/users/me/settings/
     Response: {
       "notifications_enabled": true,
       "email_updates": true,
       "privacy_level": "public|private"
     }
```

#### Update Settings
```
PATCH /api/v1/users/me/settings/
      {
        "notifications_enabled": true,
        "email_updates": false,
        "privacy_level": "private"
      }
      Response: Updated settings
```

#### Change Password
```
POST /api/v1/auth/change-password/
     {
       "current_password": "old_pass",
       "new_password": "new_pass"
     }
     Response: {success: true}
```

#### Delete Account
```
DELETE /api/v1/users/me/
       Response: {success: true}
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL (FK to auth.users),
    username VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    full_name VARCHAR(200),
    email VARCHAR(255),
    avatar_url TEXT,
    bio TEXT,
    tier VARCHAR(50) DEFAULT 'free',
    reputation INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    is_creator BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Posts Table
```sql
CREATE TABLE posts (
    id UUID PRIMARY KEY,
    author_id UUID NOT NULL (FK to users.user_id),
    content TEXT NOT NULL,
    media_url TEXT,
    media_type VARCHAR(50),
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    httn_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Wallets Table
```sql
CREATE TABLE wallets (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL (FK to users.user_id),
    httn_points INTEGER DEFAULT 0,
    httn_tokens DECIMAL(10,2) DEFAULT 0,
    espees DECIMAL(10,2) DEFAULT 0,
    pending_rewards INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Post Interactions Table
```sql
CREATE TABLE post_interactions (
    id UUID PRIMARY KEY,
    post_id UUID NOT NULL (FK to posts.id),
    user_id UUID NOT NULL (FK to users.user_id),
    interaction_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Authentication Flow

### 1. Signup Flow
```
Client → POST /api/v1/auth/signup
  ↓
Server → Create auth user + user profile
  ↓
Server → Create wallet record
  ↓
Server → Send JWT token to client
  ↓
Client → Store token in localStorage
```

### 2. Login Flow
```
Client → POST /api/v1/auth/signin
  ↓
Server → Validate credentials
  ↓
Server → Check user profile exists
  ↓
Server → Generate JWT token
  ↓
Client → Store token
  ↓
Client → Use token for all subsequent requests
```

### 3. Token Refresh
```
Client → Detect token expiry or 401 error
  ↓
Client → POST /api/v1/auth/refresh with refresh token
  ↓
Server → Validate refresh token
  ↓
Server → Issue new access token
  ↓
Client → Retry original request with new token
```

---

## Rate Limiting & Pagination

### Pagination Query Parameters
```
?page=1          # Page number (default: 1)
?limit=20        # Items per page (default: 20, max: 100)
?sort=-created_at  # Sort by field (- for descending)
```

### Response Format (Paginated)
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1000,
    "total_pages": 50
  }
}
```

### Rate Limiting Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640000000
```

---

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing required field: content",
    "details": {
      "field": "content",
      "reason": "required"
    }
  }
}
```

### Common HTTP Status Codes
```
200 OK              - Successful request
201 Created         - Resource created
204 No Content      - Successful request with no response body
400 Bad Request     - Invalid request parameters
401 Unauthorized    - Missing/invalid authentication
403 Forbidden       - Authenticated but not authorized
404 Not Found       - Resource doesn't exist
409 Conflict        - Resource already exists
429 Too Many        - Rate limit exceeded
500 Server Error    - Internal server error
```

---

## Priority Implementation Order

1. **Phase 1 (MVP)**
   - Authentication (signup/signin)
   - Users (profile, get, update)
   - Posts (CRUD)
   - Wallets (get balance, transactions)

2. **Phase 2**
   - Post interactions (likes, reposts, bookmarks)
   - Comments
   - Notifications
   - Follow/Followers

3. **Phase 3**
   - Communities
   - Causes
   - Tasks/Gamification
   - Live Streams

4. **Phase 4**
   - News
   - Admin Dashboard
   - e-Store
   - Advanced features

---

## Security Considerations

1. **Authentication**
   - Use JWT with expiry (1 hour)
   - Refresh tokens valid for 7 days
   - Store tokens in HTTP-only cookies (optional)

2. **Authorization**
   - Implement role-based access control (RBAC)
   - Verify user owns resource before update/delete
   - Admin endpoints require admin role

3. **Data Protection**
   - Hash passwords with bcrypt
   - Encrypt sensitive data (wallet balances)
   - Use HTTPS for all requests
   - Implement CORS properly

4. **Rate Limiting**
   - 1000 requests per hour per user
   - 100 requests per minute for writes
   - Implement exponential backoff

---

## Testing Requirements

- Unit tests for all endpoints
- Integration tests for workflows
- Load testing (1000+ concurrent users)
- Security testing (OWASP Top 10)
- API documentation with Swagger/OpenAPI

---

## Deployment Checklist

- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] Authentication service running
- [ ] Redis cache configured
- [ ] Email service configured
- [ ] Storage service (S3) configured
- [ ] Logging & monitoring enabled
- [ ] SSL certificates installed
- [ ] CORS configured
- [ ] Rate limiting enabled
- [ ] Backups configured

---

**Document Version**: 1.0  
**Last Updated**: February 26, 2026  
**Status**: Ready for Django Backend Implementation
