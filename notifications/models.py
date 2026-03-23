
from django.db import models
from users.models import User
import uuid

class Notification(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user_id = models.ForeignKey(User, on_delete=models.CASCADE)
	notification_type = models.CharField(
		max_length=20,
		choices=[('like', 'Like'), ('comment', 'Comment'), ('follow', 'Follow'), ('share', 'Share'), ('reward', 'Reward'), ('system', 'System')],
	)
	title = models.CharField(max_length=200)
	message = models.TextField()
	related_resource_type = models.CharField(max_length=50, blank=True, null=True)
	related_resource_id = models.CharField(max_length=100, blank=True, null=True)
	# Actor — the user who triggered this notification
	actor_id = models.CharField(max_length=100, blank=True, null=True)
	actor_name = models.CharField(max_length=200, blank=True, null=True)
	actor_avatar = models.URLField(blank=True, null=True)
	actor_verified = models.BooleanField(default=False)
	read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.title} - {self.user_id.username}"
