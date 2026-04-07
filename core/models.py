# core/models.py
import uuid
from django.db import models
from django.contrib.auth.models import User

class Profiles(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.IntegerField()  # Integer to match Django's auth_user.id
    username = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    display_name = models.TextField(blank=True, null=True)
    verified = models.BooleanField(default=False)
    pro_status = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avatar_url = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'profiles'
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return self.username


class Posts(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Profiles, on_delete=models.DO_NOTHING, blank=True, null=True, db_column='user_id')
    author_id = models.UUIDField(blank=True, null=True)
    content = models.TextField()
    
    # NEW MEDIA FIELDS - Add these
    media_url = models.URLField(blank=True, null=True)  # URL to image/video
    media_type = models.CharField(
        max_length=10, 
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('video', 'Video'),
            ('reel', 'Reel')
        ],
        default='text',
        blank=True,
        null=True
    )
    
    parent = models.ForeignKey('self', on_delete=models.DO_NOTHING, blank=True, null=True, db_column='parent_id')
    is_sponsored = models.BooleanField(blank=True, null=True, default=False)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    likes_count = models.IntegerField(blank=True, null=True, default=0)
    replies_count = models.IntegerField(blank=True, null=True, default=0)
    reposts_count = models.IntegerField(blank=True, null=True, default=0)

    class Meta:
        managed = False
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return f"Post {self.id} by {self.user.username if self.user else 'Unknown'}"

class Likes(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Posts, on_delete=models.DO_NOTHING, blank=True, null=True, db_column='post_id')
    user = models.ForeignKey(Profiles, on_delete=models.DO_NOTHING, blank=True, null=True, db_column='user_id')
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'likes'
        unique_together = (('post', 'user'),)
        verbose_name = 'Like'
        verbose_name_plural = 'Likes'

    def __str__(self):
        return f"Like {self.id}"


class Reposts(models.Model):
    id = models.AutoField(primary_key=True)
    original_post = models.ForeignKey(Posts, on_delete=models.DO_NOTHING, blank=True, null=True, db_column='original_post_id', related_name='reposts')
    user = models.ForeignKey(Profiles, on_delete=models.DO_NOTHING, blank=True, null=True, db_column='user_id')
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'reposts'
        unique_together = (('original_post', 'user'),)
        verbose_name = 'Repost'
        verbose_name_plural = 'Reposts'

    def __str__(self):
        return f"Repost {self.id}"


class Hashtags(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'hashtags'
        verbose_name = 'Hashtag'
        verbose_name_plural = 'Hashtags'

    def __str__(self):
        return self.name


class PostHashtags(models.Model):
    post = models.ForeignKey(Posts, on_delete=models.DO_NOTHING, db_column='post_id')
    hashtag = models.ForeignKey(Hashtags, on_delete=models.DO_NOTHING, db_column='hashtag_id')

    class Meta:
        managed = False
        db_table = 'post_hashtags'
        unique_together = (('post', 'hashtag'),)
        verbose_name = 'Post Hashtag'
        verbose_name_plural = 'Post Hashtags'

    def __str__(self):
        return f"{self.post} - {self.hashtag}"


class Transactions(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Profiles, on_delete=models.DO_NOTHING, blank=True, null=True, db_column='user_id')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20)  # 'reward', 'spend', 'stake'
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'

    def __str__(self):
        return f"{self.type}: {self.amount} ({self.user})"


class News(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'news'
        verbose_name = 'News'
        verbose_name_plural = 'News'

    def __str__(self):
        return self.title


class Communities(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'communities'
        verbose_name = 'Community'
        verbose_name_plural = 'Communities'

    def __str__(self):
        return self.name


class UserCommunities(models.Model):
    user = models.ForeignKey(Profiles, on_delete=models.DO_NOTHING, db_column='user_id')
    community = models.ForeignKey(Communities, on_delete=models.DO_NOTHING, db_column='community_id')

    class Meta:
        managed = False
        db_table = 'user_communities'
        unique_together = (('user', 'community'),)
        verbose_name = 'User Community'
        verbose_name_plural = 'User Communities'

    def __str__(self):
        return f"{self.user} - {self.community}"


class Causes(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'causes'
        verbose_name = 'Cause'
        verbose_name_plural = 'Causes'

    def __str__(self):
        return self.name


class UserCauses(models.Model):
    user = models.ForeignKey(Profiles, on_delete=models.DO_NOTHING, db_column='user_id')
    cause = models.ForeignKey(Causes, on_delete=models.DO_NOTHING, db_column='cause_id')

    class Meta:
        managed = False
        db_table = 'user_causes'
        unique_together = (('user', 'cause'),)
        verbose_name = 'User Cause'
        verbose_name_plural = 'User Causes'

    def __str__(self):
        return f"{self.user} - {self.cause}"


class Notifications(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Profiles, on_delete=models.DO_NOTHING, blank=True, null=True, db_column='user_id')
    type = models.CharField(max_length=20)  # 'like', 'reply', 'reward'
    content = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(blank=True, null=True, default=False)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.type}: {self.content[:50]}"


class AdCampaigns(models.Model):
    id = models.UUIDField(primary_key=True)
    user_id = models.UUIDField()
    title = models.TextField()
    description = models.TextField(blank=True, null=True)
    budget_points = models.IntegerField()
    spent_points = models.IntegerField()
    impressions = models.IntegerField()
    clicks = models.IntegerField()
    target_audience = models.JSONField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ad_campaigns'
        verbose_name = 'Ad Campaign'
        verbose_name_plural = 'Ad Campaigns'

    def __str__(self):
        return self.title


class PostInteractions(models.Model):
    id = models.UUIDField(primary_key=True)
    post = models.ForeignKey(Posts, on_delete=models.DO_NOTHING)
    user_id = models.UUIDField()
    interaction_type = models.TextField()
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'post_interactions'
        unique_together = (('post', 'user_id', 'interaction_type'),)
        verbose_name = 'Post Interaction'
        verbose_name_plural = 'Post Interactions'

    def __str__(self):
        return f"{self.interaction_type} on {self.post}"


class UserRoles(models.Model):
    id = models.UUIDField(primary_key=True)
    user_id = models.UUIDField()
    role = models.TextField()

    class Meta:
        managed = False
        db_table = 'user_roles'
        unique_together = (('user_id', 'role'),)
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'

    def __str__(self):
        return f"{self.user_id}: {self.role}"


class UserSettings(models.Model):
    id = models.UUIDField(primary_key=True)
    user_id = models.UUIDField(unique=True)
    email_notifications = models.BooleanField(blank=True, null=True)
    push_notifications = models.BooleanField(blank=True, null=True)
    theme = models.TextField(blank=True, null=True)
    language = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'user_settings'
        verbose_name = 'User Setting'
        verbose_name_plural = 'User Settings'

    def __str__(self):
        return f"Settings for user {self.user_id}"


class UserTasks(models.Model):
    id = models.UUIDField(primary_key=True)
    user_id = models.UUIDField()
    task_type = models.TextField()
    title = models.TextField()
    description = models.TextField(blank=True, null=True)
    reward = models.IntegerField()
    progress = models.IntegerField()
    target = models.IntegerField()
    completed = models.BooleanField()
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'user_tasks'
        verbose_name = 'User Task'
        verbose_name_plural = 'User Tasks'

    def __str__(self):
        return f"{self.title} ({'Completed' if self.completed else 'In Progress'})"


class Wallets(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Profiles, on_delete=models.CASCADE, db_column='user_id')  # This links to profiles
    httn_points = models.IntegerField(default=0)
    httn_tokens = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    espees = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    pending_rewards = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'wallets'
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'

    def __str__(self):
        return f"Wallet for {self.user.username}"


# Add these to your existing core/models.py

class Comment(models.Model):
    """Comments on posts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='comments', db_column='post_id')
    author = models.ForeignKey(Profiles, on_delete=models.CASCADE, db_column='author_id')
    content = models.TextField()
    likes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'comments'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.id}"


class Follow(models.Model):
    """Follow relationships between users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(Profiles, on_delete=models.CASCADE, related_name='following', db_column='follower_id')
    following = models.ForeignKey(Profiles, on_delete=models.CASCADE, related_name='followers', db_column='following_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'follows'
        unique_together = (('follower', 'following'),)
        verbose_name = 'Follow'
        verbose_name_plural = 'Follows'

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Bookmark(models.Model):
    """Bookmarked posts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Profiles, on_delete=models.CASCADE, db_column='user_id')
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, db_column='post_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'bookmarks'
        unique_together = (('user', 'post'),)
        verbose_name = 'Bookmark'
        verbose_name_plural = 'Bookmarks'

    def __str__(self):
        return f"{self.user.username} bookmarked post {self.post.id}"


class NewsArticle(models.Model):
    """News articles with extended fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    source = models.CharField(max_length=100, default='Herald Social')
    source_type = models.CharField(max_length=50, default='herald')
    content = models.TextField()
    category = models.CharField(max_length=50)
    source_url = models.URLField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    likes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'news_articles'
        ordering = ['-created_at']
        verbose_name = 'News Article'
        verbose_name_plural = 'News Articles'

    def __str__(self):
        return self.title


class NewsLike(models.Model):
    """Likes on news articles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Profiles, on_delete=models.CASCADE, db_column='user_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'news_likes'
        unique_together = (('article', 'user'),)
        verbose_name = 'News Like'
        verbose_name_plural = 'News Likes'

    def __str__(self):
        return f"{self.user.username} liked {self.article.title}"


class NewsBookmark(models.Model):
    """Bookmarked news articles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(Profiles, on_delete=models.CASCADE, db_column='user_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'news_bookmarks'
        unique_together = (('article', 'user'),)
        verbose_name = 'News Bookmark'
        verbose_name_plural = 'News Bookmarks'

    def __str__(self):
        return f"{self.user.username} bookmarked {self.article.title}"
