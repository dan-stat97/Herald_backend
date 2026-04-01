from django.db import models
from users.models import User
import uuid

class Cause(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=200)
	description = models.TextField()
	category = models.CharField(max_length=50)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_causes')
	goal_amount = models.DecimalField(max_digits=12, decimal_places=2)
	raised_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	image_url = models.URLField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=[('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='active')
	created_at = models.DateTimeField(auto_now_add=True)
	end_date = models.DateField(null=True, blank=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.title


class Donation(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	cause = models.ForeignKey(Cause, on_delete=models.CASCADE, related_name='donations')
	donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	message = models.TextField(blank=True, null=True)
	is_anonymous = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.donor.username} → {self.cause.title} ({self.amount})"
