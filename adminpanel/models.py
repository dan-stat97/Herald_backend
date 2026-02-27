
from django.db import models
from users.models import User
import uuid

class AdminReport(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	resource_type = models.CharField(max_length=20, choices=[('post', 'Post'), ('comment', 'Comment'), ('user', 'User')])
	resource_id = models.CharField(max_length=100)
	reason = models.CharField(max_length=100)
	description = models.TextField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

class Ban(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	reason = models.CharField(max_length=200)
	banned_until = models.DateField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

# Create your models here.
