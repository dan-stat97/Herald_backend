
from django.contrib import admin
from .models import Wallet

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
	list_display = ("id", "user_id", "httn_points", "httn_tokens", "espees", "pending_rewards", "created_at")
	search_fields = ("user_id__username",)

# Register your models here.
