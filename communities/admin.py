
from django.contrib import admin
from .models import Community

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "category", "created_by", "is_private", "member_count", "created_at")
	search_fields = ("name", "category")

# Register your models here.
