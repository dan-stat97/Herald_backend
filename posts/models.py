
from django.db import models
from users.models import User
import uuid

class Post(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	author_id = models.ForeignKey(User, to_field='user_id', on_delete=models.CASCADE)
	content = models.TextField()
	media_url = models.URLField(null=True, blank=True)
	media_type = models.CharField(max_length=20, choices=[('image', 'Image'), ('video', 'Video'), ('reel', 'Reel')], null=True, blank=True)
	likes_count = models.IntegerField(default=0)
	comments_count = models.IntegerField(default=0)
	shares_count = models.IntegerField(default=0)
	httn_earned = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.author_id.username}: {self.content[:30]}"

# Create your models here.
