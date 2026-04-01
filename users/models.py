from django.db import models
from django.contrib.auth import get_user_model
import uuid

UserAuth = get_user_model()


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.OneToOneField(UserAuth, on_delete=models.CASCADE, unique=True)
    username = models.CharField(unique=True, max_length=100)
    display_name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField()
    avatar_url = models.URLField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    notifications_enabled = models.BooleanField(default=True)
    privacy_level = models.CharField(
        max_length=20,
        choices=[('public', 'Public'), ('private', 'Private'), ('friends_only', 'Friends Only')],
        default='public',
    )
    email_updates = models.BooleanField(default=True)
    interests = models.JSONField(default=list, blank=True)
    onboarding_completed = models.BooleanField(default=False)
    tier = models.CharField(max_length=20, choices=[('free', 'Free'), ('creator', 'Creator'), ('premium', 'Premium')], default='free')
    reputation = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_creator = models.BooleanField(default=False)
    auth_provider = models.CharField(max_length=32, default='password')
    kingschat_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    kingschat_username = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


class DirectMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'direct_messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}"
