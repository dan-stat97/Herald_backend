from django.db import models
from users.models import User
import uuid


class LiveStream(models.Model):
    """Live streaming model"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('ended', 'Ended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streams')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    stream_url = models.URLField(null=True, blank=True)
    thumbnail_url = models.URLField(null=True, blank=True)
    viewer_count = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'live_streams'
        ordering = ['-created_at']
    
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

    def __str__(self):
        return f"{self.user.username} {self.event_type} {self.stream.title}"
