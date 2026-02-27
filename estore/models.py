
from django.db import models
from users.models import User
import uuid

class Product(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=200)
	description = models.TextField(null=True, blank=True)
	category = models.CharField(max_length=100)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	image_url = models.URLField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

class Cart(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	items = models.JSONField(default=list)
	total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	created_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user_id = models.ForeignKey(User, on_delete=models.CASCADE)
	items = models.JSONField()
	total_amount = models.DecimalField(max_digits=10, decimal_places=2)
	payment_type = models.CharField(max_length=20, choices=[('card', 'Card'), ('wallet', 'Wallet'), ('crypto', 'Crypto')])
	status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('cancelled', 'Cancelled')])
	created_at = models.DateTimeField(auto_now_add=True)
	completed_at = models.DateTimeField(null=True, blank=True)

# Create your models here.
