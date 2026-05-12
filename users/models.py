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
    cover_url = models.URLField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    phone_number = models.CharField(max_length=32, null=True, blank=True)
    notifications_enabled = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    privacy_level = models.CharField(
        max_length=20,
        choices=[('public', 'Public'), ('followers', 'Followers Only'), ('private', 'Private')],
        default='public',
    )
    email_updates = models.BooleanField(default=True)
    discover_by_email = models.BooleanField(default=True)
    discover_by_phone = models.BooleanField(default=True)
    allow_message_requests = models.BooleanField(default=False)
    show_read_receipts = models.BooleanField(default=True)
    display_sensitive_media = models.BooleanField(default=False)
    mark_media_sensitive = models.BooleanField(default=False)
    personalization_enabled = models.BooleanField(default=True)
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
    MESSAGE_KIND_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('gif', 'GIF'),
        ('file', 'File'),
        ('audio_call', 'Audio Call'),
        ('video_call', 'Video Call'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True, default='')
    kind = models.CharField(max_length=20, choices=MESSAGE_KIND_CHOICES, default='text')
    attachments = models.JSONField(default=list, blank=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='thread_replies')
    forwarded_from = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='forwards')
    reactions = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_for_sender = models.BooleanField(default=False)
    deleted_for_recipient = models.BooleanField(default=False)
    deleted_for_everyone_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'direct_messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}"


class PinnedConversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pinned_conversations')
    peer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pinned_by_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pinned_conversations'
        ordering = ['created_at']
        unique_together = [('owner', 'peer')]

    def __str__(self):
        return f"{self.owner.username} pinned {self.peer.username}"


class DevicePushToken(models.Model):
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
        ('unknown', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_tokens')
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='unknown')
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'device_push_tokens'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} ({self.platform})"


class CallSession(models.Model):
    MODE_CHOICES = [
        ('audio', 'Audio'),
        ('video', 'Video'),
    ]
    STATUS_CHOICES = [
        ('ringing', 'Ringing'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
        ('canceled', 'Canceled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_calls')
    callee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_calls')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='audio')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ringing')
    room_name = models.CharField(max_length=120)
    room_url = models.URLField()
    related_message = models.ForeignKey(DirectMessage, null=True, blank=True, on_delete=models.SET_NULL, related_name='call_sessions')
    caller_muted = models.BooleanField(default=False)
    caller_video_enabled = models.BooleanField(default=True)
    callee_muted = models.BooleanField(default=False)
    callee_video_enabled = models.BooleanField(default=True)
    started_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'call_sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.caller.username} -> {self.callee.username} ({self.mode}, {self.status})"
