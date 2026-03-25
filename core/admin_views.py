from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
from django.db import connection
from django.utils import timezone
from datetime import timedelta


@method_decorator(staff_member_required, name='dispatch')
class AdminDashboardView(View):
    def get(self, request):
        from posts.models import Post, Comment

        # --- User stats ---
        try:
            from users.models import User as UserProfile
            total_users = UserProfile.objects.count()
            verified_users = UserProfile.objects.filter(is_verified=True).count()
            creator_users = UserProfile.objects.filter(is_creator=True).count()
            tier_counts = {
                t: UserProfile.objects.filter(tier=t).count()
                for t in ['free', 'creator', 'premium']
            }
        except Exception:
            total_users = verified_users = creator_users = 0
            tier_counts = {}

        # --- Post stats ---
        now = timezone.now()
        total_posts = Post.objects.count()
        total_comments = Comment.objects.count()
        posts_today = Post.objects.filter(created_at__date=now.date()).count()
        posts_week = Post.objects.filter(created_at__gte=now - timedelta(days=7)).count()
        posts_month = Post.objects.filter(created_at__gte=now - timedelta(days=30)).count()
        recent_posts = Post.objects.select_related('author_id', 'author_id__user_id').order_by('-created_at')[:10]

        # --- Wallet / HTTN stats ---
        try:
            from wallets.models import Wallet
            wallets = Wallet.objects.all()[:5000]
            total_httn_points = sum(getattr(w, 'httn_points', 0) for w in wallets)
        except Exception:
            total_httn_points = 0

        # --- Ad stats ---
        try:
            from adminpanel.models import AdCampaign
            total_ads = AdCampaign.objects.count()
            active_ads = AdCampaign.objects.filter(status='active').count()
            total_impressions = sum(AdCampaign.objects.values_list('impressions', flat=True))
            total_clicks = sum(AdCampaign.objects.values_list('clicks', flat=True))
        except Exception:
            total_ads = active_ads = total_impressions = total_clicks = 0

        context = {
            'title': 'Platform Dashboard',
            'total_users': total_users,
            'verified_users': verified_users,
            'creator_users': creator_users,
            'tier_counts': tier_counts,
            'total_posts': total_posts,
            'total_comments': total_comments,
            'posts_today': posts_today,
            'posts_week': posts_week,
            'posts_month': posts_month,
            'recent_posts': recent_posts,
            'total_httn_points': total_httn_points,
            'total_ads': total_ads,
            'active_ads': active_ads,
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
        }
        return render(request, 'admin/dashboard.html', context)


@method_decorator(staff_member_required, name='dispatch')
class DBTestView(View):
    def get(self, request):
        core_tables = [
            ('auth_user', 'Auth Users'),
            ('users_user', 'User Profiles'),
            ('posts_post', 'Posts'),
            ('posts_comment', 'Comments'),
            ('posts_postlike', 'Post Likes'),
            ('posts_postrepost', 'Post Reposts'),
            ('posts_postbookmark', 'Post Bookmarks'),
        ]
        optional_tables = [
            ('wallets_wallet', 'Wallets'),
            ('adminpanel_adcampaign', 'Ad Campaigns'),
            ('adminpanel_ban', 'User Bans'),
            ('adminpanel_adminreport', 'Reports'),
            ('direct_messages', 'Direct Messages'),
        ]

        results = []
        overall_ok = True

        with connection.cursor() as cursor:
            for table_name, label in core_tables + optional_tables:
                is_core = table_name in [t[0] for t in core_tables]
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                    count = cursor.fetchone()[0]
                    results.append({
                        'table': table_name, 'label': label,
                        'count': count, 'ok': True, 'error': None, 'core': is_core,
                    })
                except Exception as e:
                    results.append({
                        'table': table_name, 'label': label,
                        'count': 0, 'ok': False, 'error': str(e)[:120], 'core': is_core,
                    })
                    if is_core:
                        overall_ok = False

        db_settings = connection.settings_dict
        db_info = {
            'engine': db_settings.get('ENGINE', '').split('.')[-1],
            'name': db_settings.get('NAME', ''),
            'host': db_settings.get('HOST', 'localhost') or 'localhost',
        }

        context = {
            'title': 'Database Health Check',
            'results': results,
            'overall_ok': overall_ok,
            'db_info': db_info,
        }
        return render(request, 'admin/db_test.html', context)
