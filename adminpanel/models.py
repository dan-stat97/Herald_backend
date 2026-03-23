
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


class AdCampaign(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ad_campaigns')
	title = models.CharField(max_length=200)
	description = models.TextField(null=True, blank=True)
	# Display fields for rendering the ad banner
	image_url = models.URLField(null=True, blank=True)
	cta_text = models.CharField(max_length=100, default='Learn More')
	target_url = models.URLField(null=True, blank=True)
	sponsor_name = models.CharField(max_length=200, null=True, blank=True)
	reward_points = models.IntegerField(default=5)
	is_featured = models.BooleanField(default=False)
	# Budget & metrics
	budget_points = models.IntegerField(default=0)
	spent_points = models.IntegerField(default=0)
	impressions = models.IntegerField(default=0)
	clicks = models.IntegerField(default=0)
	status = models.CharField(max_length=20, choices=[('active', 'Active'), ('paused', 'Paused'), ('completed', 'Completed')], default='active')
	start_date = models.DateField(null=True, blank=True)
	end_date = models.DateField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

# Create your models here.
