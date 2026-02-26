# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Profiles, Posts, Likes, Reposts, Hashtags, PostHashtags,
    Transactions, News, Communities, UserCommunities, Causes,
    UserCauses, Notifications, AdCampaigns, PostInteractions,
    UserRoles, UserSettings, UserTasks, Wallets
)

# ========== PROFILE ADMIN ==========
@admin.register(Profiles)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'user_id', 'full_name', 'verified', 'pro_status', 'balance', 'created_at']
    list_display_links = ['id', 'username']
    list_filter = ['verified', 'pro_status', 'created_at']
    search_fields = ['username', 'full_name', 'display_name']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('User Information', {
            'fields': ('id', 'user_id', 'username', 'full_name', 'display_name')
        }),
        ('Status', {
            'fields': ('verified', 'pro_status', 'balance')
        }),
        ('Media', {
            'fields': ('avatar_url',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


# ========== POSTS ADMIN ==========
@admin.register(Posts)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'content_preview', 'is_sponsored', 'likes_count', 'replies_count', 'reposts_count', 'created_at']
    list_display_links = ['id', 'content_preview']
    list_filter = ['is_sponsored', 'created_at']
    search_fields = ['content', 'user__username']
    readonly_fields = ['id', 'created_at', 'likes_count', 'replies_count', 'reposts_count']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


# ========== LIKES ADMIN ==========
@admin.register(Likes)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['post__content', 'user__username']
    readonly_fields = ['id', 'created_at']


# ========== REPOSTS ADMIN ==========
@admin.register(Reposts)
class RepostAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_post', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['original_post__content', 'user__username']
    readonly_fields = ['id', 'created_at']


# ========== HASHTAGS ADMIN ==========
@admin.register(Hashtags)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


# ========== POST HASHTAGS ADMIN ==========
@admin.register(PostHashtags)
class PostHashtagAdmin(admin.ModelAdmin):
    list_display = ['post', 'hashtag']
    list_filter = ['hashtag']
    search_fields = ['post__content', 'hashtag__name']


# ========== TRANSACTIONS ADMIN ==========
@admin.register(Transactions)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'type', 'description', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['id', 'created_at']


# ========== NEWS ADMIN ==========
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['id', 'created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if obj.content and len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


# ========== COMMUNITIES ADMIN ==========
@admin.register(Communities)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description_preview']
    search_fields = ['name', 'description']
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if obj.description and len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'


# ========== USER COMMUNITIES ADMIN ==========
@admin.register(UserCommunities)
class UserCommunityAdmin(admin.ModelAdmin):
    list_display = ['user', 'community']
    list_filter = ['community']
    search_fields = ['user__username', 'community__name']


# ========== CAUSES ADMIN ==========
@admin.register(Causes)
class CauseAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description_preview']
    search_fields = ['name', 'description']
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if obj.description and len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'


# ========== USER CAUSES ADMIN ==========
@admin.register(UserCauses)
class UserCauseAdmin(admin.ModelAdmin):
    list_display = ['user', 'cause']
    list_filter = ['cause']
    search_fields = ['user__username', 'cause__name']


# ========== NOTIFICATIONS ADMIN ==========
@admin.register(Notifications)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type', 'content_preview', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['id', 'created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if obj.content and len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


# ========== AD CAMPAIGNS ADMIN ==========
@admin.register(AdCampaigns)
class AdCampaignAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user_id', 'budget_points', 'spent_points', 'impressions', 'clicks', 'status']
    list_filter = ['status']
    search_fields = ['title', 'description']


# ========== POST INTERACTIONS ADMIN ==========
@admin.register(PostInteractions)
class PostInteractionAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'user_id', 'interaction_type', 'created_at']
    list_filter = ['interaction_type', 'created_at']
    search_fields = ['post__content']


# ========== USER ROLES ADMIN ==========
@admin.register(UserRoles)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'role']
    list_filter = ['role']
    search_fields = ['user_id']


# ========== USER SETTINGS ADMIN ==========
@admin.register(UserSettings)
class UserSettingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'theme', 'language', 'email_notifications', 'push_notifications']
    list_filter = ['theme', 'language', 'email_notifications', 'push_notifications']
    search_fields = ['user_id']


# ========== USER TASKS ADMIN ==========
@admin.register(UserTasks)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'task_type', 'title', 'progress', 'target', 'completed', 'reward']
    list_filter = ['task_type', 'completed']
    search_fields = ['title', 'description']


# ========== WALLETS ADMIN ==========
@admin.register(Wallets)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'httn_points', 'httn_tokens', 'espees', 'pending_rewards']
    search_fields = ['user_id']


# ========== CUSTOMIZE USER ADMIN ==========
class CustomUserAdmin(UserAdmin):
    list_display = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
    list_display_links = ['id', 'username']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['id', 'date_joined', 'last_login']

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ========== CUSTOMIZE ADMIN SITE HEADER ==========
admin.site.site_header = 'Herald Social Admin Dashboard'
admin.site.site_title = 'Herald Admin'
admin.site.index_title = 'Welcome to Herald Admin'