from django.contrib import admin
from django.utils.html import format_html
from .models import AdminReport, Ban, AdCampaign


@admin.register(AdminReport)
class AdminReportAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'resource_type', 'resource_id', 'reason', 'created_at']
    list_filter = ['resource_type', 'created_at']
    search_fields = ['resource_type', 'resource_id', 'reason', 'description']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    list_per_page = 25

    def id_short(self, obj):
        return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'


@admin.register(Ban)
class BanAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'user', 'reason', 'banned_until', 'created_at']
    list_filter = ['banned_until', 'created_at']
    search_fields = ['user__username', 'reason']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    list_per_page = 25

    def id_short(self, obj):
        return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'


def activate_campaigns(modeladmin, request, queryset):
    queryset.update(status='active')
activate_campaigns.short_description = '▶ Activate selected campaigns'

def pause_campaigns(modeladmin, request, queryset):
    queryset.update(status='paused')
pause_campaigns.short_description = '⏸ Pause selected campaigns'

def complete_campaigns(modeladmin, request, queryset):
    queryset.update(status='completed')
complete_campaigns.short_description = '✓ Mark selected campaigns as completed'


@admin.register(AdCampaign)
class AdCampaignAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 'title', 'advertiser', 'status_badge',
        'impressions', 'clicks', 'ctr_display',
        'budget_points', 'spent_points', 'is_featured',
        'start_date', 'end_date', 'created_at',
    ]
    list_filter = ['status', 'is_featured', 'created_at', 'start_date']
    search_fields = ['title', 'description', 'sponsor_name', 'target_url', 'user__username']
    readonly_fields = ['id', 'impressions', 'clicks', 'spent_points', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 20
    actions = [activate_campaigns, pause_campaigns, complete_campaigns]

    fieldsets = (
        ('Campaign Info', {
            'fields': ('id', 'user', 'title', 'description', 'sponsor_name', 'is_featured'),
        }),
        ('Creative', {
            'fields': ('image_url', 'cta_text', 'target_url', 'reward_points'),
        }),
        ('Budget & Schedule', {
            'fields': ('budget_points', 'spent_points', 'start_date', 'end_date', 'status'),
        }),
        ('Metrics (read-only)', {
            'fields': ('impressions', 'clicks'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def id_short(self, obj):
        return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'

    def advertiser(self, obj):
        try:
            return obj.user.username
        except Exception:
            return '—'
    advertiser.short_description = 'Advertiser'

    def status_badge(self, obj):
        colours = {
            'active': '#22c55e',
            'paused': '#f59e0b',
            'completed': '#6b7280',
        }
        colour = colours.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color:{};font-weight:600;">● {}</span>',
            colour, obj.status.title()
        )
    status_badge.short_description = 'Status'

    def ctr_display(self, obj):
        if obj.impressions == 0:
            return '—'
        ctr = (obj.clicks / obj.impressions) * 100
        return f'{ctr:.1f}%'
    ctr_display.short_description = 'CTR'
