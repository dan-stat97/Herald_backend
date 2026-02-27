
from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
	list_display = ("id", "author_id", "content", "media_type", "likes_count", "comments_count", "shares_count", "httn_earned", "created_at")
	search_fields = ("content",)

# Register your models here.
