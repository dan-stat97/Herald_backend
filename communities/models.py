from django.db import models
from users.models import User
import uuid


class Community(models.Model):
    MEMBERSHIP_OPEN    = 'open'
    MEMBERSHIP_REQUEST = 'request'
    MEMBERSHIP_INVITE  = 'invite'
    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_OPEN,    'Open'),
        (MEMBERSHIP_REQUEST, 'Request to Join'),
        (MEMBERSHIP_INVITE,  'Invite Only'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name            = models.CharField(max_length=200)
    description     = models.TextField(null=True, blank=True)
    category        = models.CharField(max_length=50, default='general')
    created_by      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_communities')
    image_url       = models.URLField(null=True, blank=True)
    rules           = models.JSONField(default=list, blank=True)
    is_private      = models.BooleanField(default=False)  # legacy — keep for migration safety
    membership_type = models.CharField(max_length=10, choices=MEMBERSHIP_CHOICES, default=MEMBERSHIP_OPEN)
    entry_question  = models.TextField(null=True, blank=True)
    member_count    = models.IntegerField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CommunityMember(models.Model):
    ROLE_MEMBER    = 'member'
    ROLE_MODERATOR = 'moderator'
    ROLE_ADMIN     = 'admin'
    ROLE_CHOICES   = [
        (ROLE_MEMBER,    'Member'),
        (ROLE_MODERATOR, 'Moderator'),
        (ROLE_ADMIN,     'Admin'),
    ]

    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_memberships')
    role      = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('community', 'user')
        db_table = 'community_members'

    def __str__(self):
        return f"{self.user.username} in {self.community.name} ({self.role})"


class CommunityJoinRequest(models.Model):
    STATUS_PENDING  = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES  = [
        (STATUS_PENDING,  'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community   = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='join_requests')
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_join_requests')
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    answer      = models.TextField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('community', 'user')

    def __str__(self):
        return f"{self.user.username} → {self.community.name} [{self.status}]"


class CommunityPost(models.Model):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community      = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts')
    author         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    content        = models.TextField()
    media_url      = models.URLField(null=True, blank=True)
    media_type     = models.CharField(max_length=20, null=True, blank=True)
    likes_count    = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    views_count    = models.IntegerField(default=0)
    is_pinned      = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.author.username}: {self.content[:50]}"


class CommunityPostLike(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post       = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='likes')
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')


class CommunityPostComment(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post       = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_post_comments')
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username}: {self.content[:40]}"


class CommunityInvite(models.Model):
    STATUS_PENDING  = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_CHOICES  = [
        (STATUS_PENDING,  'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community    = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='invites')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_invites')
    invited_by   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_community_invites')
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at   = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('community', 'invited_user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invited_by.username} -> {self.invited_user.username} for {self.community.name} [{self.status}]"
