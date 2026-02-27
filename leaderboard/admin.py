
from django.contrib import admin
from .models import UserRank

@admin.register(UserRank)
class UserRankAdmin(admin.ModelAdmin):
	list_display = ("user", "reputation", "rank")
	search_fields = ("user__username",)

# Register your models here.
