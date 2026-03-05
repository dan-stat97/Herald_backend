
from django.db import models
from users.models import User
import uuid

class Community(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=200)
	description = models.TextField(null=True, blank=True)
	category = models.CharField(max_length=50)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE)
	image_url = models.URLField(null=True, blank=True)
	is_private = models.BooleanField(default=False)
	member_count = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name


class CommunityMember(models.Model):
	"""Model to track community members"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	joined_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		unique_together = ('community', 'user')
		db_table = 'community_members'
	
	def __str__(self):
		return f"{self.user.username} in {self.community.name}"
