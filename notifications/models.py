
from django.db import models
from users.models import User
import uuid

class Notification(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user_id = models.ForeignKey(User, on_delete=models.CASCADE)
	notification_type = models.CharField(max_length=20, choices=[('like', 'Like'), ('comment', 'Comment'), ('follow', 'Follow'), ('share', 'Share')])
	title = models.CharField(max_length=200)
	message = models.TextField()
	related_resource_type = models.CharField(max_length=50)
	related_resource_id = models.CharField(max_length=100)
	read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.title} - {self.user_id.username}"

# Create your models here.
