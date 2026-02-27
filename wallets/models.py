
from django.db import models
from users.models import User
import uuid

class Wallet(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user_id = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
	httn_points = models.IntegerField(default=0)
	httn_tokens = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	espees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	pending_rewards = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Wallet of {self.user_id.username}"

# Create your models here.
