
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
	bookmarks_count = models.IntegerField(default=0)
	httn_earned = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.author_id.username}: {self.content[:30]}"

# Comment model for post comments
class Comment(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
	author = models.ForeignKey('users.User', to_field='user_id', on_delete=models.CASCADE)
	content = models.TextField()
	likes_count = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.author.username}: {self.content[:30]}"


class PostLike(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
	user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='post_likes')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('post', 'user')

	def __str__(self):
		return f"{self.user} liked {self.post_id}"


class PostRepost(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	post = models.ForeignKey(Post, related_name='reposts', on_delete=models.CASCADE)
	user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='post_reposts')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('post', 'user')

	def __str__(self):
		return f"{self.user} reposted {self.post_id}"


class PostBookmark(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	post = models.ForeignKey(Post, related_name='bookmarks', on_delete=models.CASCADE)
	user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='post_bookmarks')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('post', 'user')

	def __str__(self):
		return f"{self.user} bookmarked {self.post_id}"


class ScheduledPost(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='scheduled_posts')
	content = models.TextField(blank=True)
	media_url = models.URLField(null=True, blank=True)
	media_type = models.CharField(max_length=20, choices=[('image', 'Image'), ('video', 'Video'), ('reel', 'Reel')], null=True, blank=True)
	run_at = models.DateTimeField()
	status = models.CharField(max_length=20, choices=[('scheduled', 'Scheduled'), ('published', 'Published'), ('cancelled', 'Cancelled')], default='scheduled')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'scheduled_posts'
		ordering = ['run_at']

	def __str__(self):
		return f"Scheduled by {self.user.username} at {self.run_at.isoformat()}"
