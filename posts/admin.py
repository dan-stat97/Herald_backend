from django.contrib import admin
from .models import Post, Comment, PostLike, PostRepost, PostBookmark


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 'author_display', 'content_preview',
        'likes_count', 'comments_count', 'shares_count', 'bookmarks_count',
        'httn_earned', 'media_type', 'created_at',
    ]
    list_filter = ['created_at', 'media_type']
    search_fields = ['content', 'author_id__username', 'author_id__user_id__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'likes_count', 'comments_count', 'shares_count', 'bookmarks_count']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 25

    def id_short(self, obj):
        return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'

    def author_display(self, obj):
        try:
            return obj.author_id.username
        except Exception:
            return '—'
    author_display.short_description = 'Author'

    def content_preview(self, obj):
        return obj.content[:70] + ('…' if len(obj.content) > 70 else '')
    content_preview.short_description = 'Content'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'author_display', 'content_preview', 'likes_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 25

    def id_short(self, obj):
        return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'

    def author_display(self, obj):
        try:
            return obj.author.username
        except Exception:
            return '—'
    author_display.short_description = 'Author'

    def content_preview(self, obj):
        return obj.content[:70] + ('…' if len(obj.content) > 70 else '')
    content_preview.short_description = 'Content'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'user_display', 'post_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    list_per_page = 50

    def id_short(self, obj): return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'

    def user_display(self, obj):
        try: return obj.user.username
        except: return '—'
    user_display.short_description = 'User'

    def post_preview(self, obj):
        return obj.post.content[:50] + '…'
    post_preview.short_description = 'Post'


@admin.register(PostRepost)
class PostRepostAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'user_display', 'post_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    list_per_page = 50

    def id_short(self, obj): return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'

    def user_display(self, obj):
        try: return obj.user.username
        except: return '—'
    user_display.short_description = 'User'

    def post_preview(self, obj): return obj.post.content[:50] + '…'
    post_preview.short_description = 'Post'


@admin.register(PostBookmark)
class PostBookmarkAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'user_display', 'post_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    list_per_page = 50

    def id_short(self, obj): return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'

    def user_display(self, obj):
        try: return obj.user.username
        except: return '—'
    user_display.short_description = 'User'

    def post_preview(self, obj): return obj.post.content[:50] + '…'
    post_preview.short_description = 'Post'
