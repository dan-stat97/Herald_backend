
from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ("id", "user_id", "notification_type", "title", "read", "created_at")
	search_fields = ("title", "user_id__username")

# Register your models here.
