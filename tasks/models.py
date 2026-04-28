from django.db import models
from users.models import User
import uuid


class Task(models.Model):
    """Task model for gamification"""
    TASK_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('campaign', 'Campaign'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    reward = models.IntegerField()  # HTTN Points reward
    target = models.IntegerField()  # Target count to complete
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tasks'
    
    def __str__(self):
        return self.title


class UserTask(models.Model):
    """User-specific task progress"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    claimed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_tasks'
        unique_together = ('user', 'task')
    
    def __str__(self):
        return f"{self.user.username} - {self.task.title}"


class RewardGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reward_grants')
    action_code = models.CharField(max_length=64)
    source_key = models.CharField(max_length=160)
    points = models.IntegerField()
    description = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reward_grants'
        unique_together = ('user', 'action_code', 'source_key')
        indexes = [
            models.Index(fields=['user', '-created_at'], name='reward_user_created_idx'),
            models.Index(fields=['action_code', '-created_at'], name='reward_action_created_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} {self.action_code} {self.points}"
