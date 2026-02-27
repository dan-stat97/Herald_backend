
from django.db import models
from users.models import User

# Example leaderboard model (expand as needed)
class UserRank(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	reputation = models.IntegerField(default=0)
	rank = models.IntegerField(default=0)

	def __str__(self):
		return f"{self.user.username} - Rank {self.rank}"

# Create your models here.
