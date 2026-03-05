
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


class Transaction(models.Model):
	"""Wallet transactions history"""
	TRANSACTION_TYPE_CHOICES = [
		('deposit', 'Deposit'),
		('withdrawal', 'Withdrawal'),
		('transfer', 'Transfer'),
		('conversion', 'Conversion'),
		('reward', 'Reward'),
		('purchase', 'Purchase'),
	]
	
	CURRENCY_CHOICES = [
		('points', 'HTTN Points'),
		('tokens', 'HTTN Tokens'),
		('espees', 'Espees'),
	]
	
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	wallet_id = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
	transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES)
	description = models.TextField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		db_table = 'wallet_transactions'
		ordering = ['-created_at']
	
	def __str__(self):
		return f"{self.transaction_type}: {self.amount} {self.currency}"

# Create your models here.
