from django.db import models
from users.models import User
import uuid

class Community(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=200)
	description = models.TextField(null=True, blank=True)
	category = models.CharField(max_length=50, default='general')
	created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_communities')
	image_url = models.URLField(null=True, blank=True)
	is_private = models.BooleanField(default=False)
	member_count = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.name


class CommunityMember(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_memberships')
	role = models.CharField(max_length=20, choices=[('member', 'Member'), ('moderator', 'Moderator'), ('admin', 'Admin')], default='member')
	joined_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('community', 'user')
		db_table = 'community_members'

	def __str__(self):
		return f"{self.user.username} in {self.community.name}"


class CommunityPost(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts')
	author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
	content = models.TextField()
	media_url = models.URLField(null=True, blank=True)
	media_type = models.CharField(max_length=20, null=True, blank=True)
	likes_count = models.IntegerField(default=0)
	comments_count = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.author.username}: {self.content[:50]}"


class CommunityPostLike(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='likes')
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('post', 'user')
