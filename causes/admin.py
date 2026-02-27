
from django.contrib import admin
from .models import Cause

@admin.register(Cause)
class CauseAdmin(admin.ModelAdmin):
	list_display = ("id", "title", "category", "created_by", "goal_amount", "raised_amount", "status", "created_at", "end_date")
	search_fields = ("title", "category")

# Register your models here.
