from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User as AuthUser
from .models import User, DirectMessage

# Re-register auth.User with better display
admin.site.unregister(AuthUser)

@admin.register(AuthUser)
class AuthUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    list_per_page = 25


def make_verified(modeladmin, request, queryset):
    queryset.update(is_verified=True)
make_verified.short_description = '✓ Mark selected users as verified'

def make_unverified(modeladmin, request, queryset):
    queryset.update(is_verified=False)
make_unverified.short_description = '✗ Remove verification from selected users'

def make_creator(modeladmin, request, queryset):
    queryset.update(is_creator=True)
make_creator.short_description = '★ Grant creator status'

def remove_creator(modeladmin, request, queryset):
    queryset.update(is_creator=False)
remove_creator.short_description = '☆ Remove creator status'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 'username', 'display_name', 'email',
        'tier', 'is_verified', 'is_creator', 'reputation', 'created_at',
    ]
    list_filter = ['tier', 'is_verified', 'is_creator', 'created_at']
    search_fields = ['username', 'display_name', 'email']
    readonly_fields = ['id', 'user_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 25
    actions = [make_verified, make_unverified, make_creator, remove_creator]

    fieldsets = (
        ('Identity', {
            'fields': ('id', 'user_id', 'username', 'display_name', 'full_name', 'email'),
        }),
        ('Profile', {
            'fields': ('avatar_url', 'bio', 'tier', 'reputation'),
        }),
        ('Status', {
            'fields': ('is_verified', 'is_creator', 'onboarding_completed'),
        }),
        ('Preferences', {
            'fields': ('notifications_enabled', 'email_updates', 'privacy_level'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def id_short(self, obj):
        return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'sender', 'recipient', 'content_preview', 'read', 'created_at']
    list_filter = ['read', 'created_at']
    search_fields = ['sender__username', 'recipient__username', 'content']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    list_per_page = 50

    def id_short(self, obj):
        return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'

    def content_preview(self, obj):
        return obj.content[:60] + ('…' if len(obj.content) > 60 else '')
    content_preview.short_description = 'Message'
