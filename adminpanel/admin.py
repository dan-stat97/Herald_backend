
from django.contrib import admin
from .models import AdminReport, Ban

@admin.register(AdminReport)
class AdminReportAdmin(admin.ModelAdmin):
	list_display = ("id", "resource_type", "resource_id", "reason", "created_at")
	search_fields = ("resource_type", "resource_id", "reason")

@admin.register(Ban)
class BanAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "reason", "banned_until", "created_at")
	search_fields = ("user__username", "reason")

# Register your models here.
