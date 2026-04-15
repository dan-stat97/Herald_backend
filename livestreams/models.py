from django.db import models
from users.models import User
import uuid


class LiveStream(models.Model):
    """Live streaming model"""
    PROVIDER_CHOICES = [
        ('manual', 'Manual'),
        ('ivs', 'Amazon IVS'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('ended', 'Ended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streams')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='manual')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    stream_url = models.URLField(null=True, blank=True)
    playback_url = models.URLField(null=True, blank=True)
    thumbnail_url = models.URLField(null=True, blank=True)
    ingest_endpoint = models.URLField(null=True, blank=True)
    provider_stream_key = models.CharField(max_length=255, null=True, blank=True)
    ivs_channel_arn = models.CharField(max_length=255, null=True, blank=True)
    ivs_stage_arn = models.CharField(max_length=255, null=True, blank=True)
    ivs_stage_rtmps_endpoint = models.URLField(null=True, blank=True)
    ivs_stage_whip_endpoint = models.URLField(null=True, blank=True)
    host_token_expires_at = models.DateTimeField(null=True, blank=True)
    viewer_count = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'live_streams'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='streams_status_created_idx'),
            models.Index(fields=['status', 'scheduled_for'], name='streams_status_sched_idx'),
            models.Index(fields=['user', 'status'], name='streams_user_status_idx'),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.status}"


class StreamChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_chat_messages')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stream_chat_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stream', '-created_at'], name='stream_chat_stream_created_idx'),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.message[:30]}"


class StreamDonation(models.Model):
    CURRENCY_CHOICES = [
        ('points', 'HTTN Points'),
        ('tokens', 'HTTN Tokens'),
        ('espees', 'Espees'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='donations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_donations')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES, default='espees')
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stream_donations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stream', '-created_at'], name='strm_don_stream_created_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} donated {self.amount} {self.currency}"


class StreamViewerEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('join', 'Join'),
        ('leave', 'Leave'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='viewer_events')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_viewer_events')
    event_type = models.CharField(max_length=10, choices=EVENT_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stream_viewer_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stream', '-created_at'], name='strm_view_stream_created_idx'),
            models.Index(fields=['user', '-created_at'], name='strm_view_user_created_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} {self.event_type} {self.stream.title}"
