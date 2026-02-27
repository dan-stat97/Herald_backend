
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ("id", "username", "display_name", "email", "tier", "reputation", "is_verified", "is_creator", "created_at")
	search_fields = ("username", "display_name", "email")

# Register your models here.
