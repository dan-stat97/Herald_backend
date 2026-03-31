from datetime import timedelta

from django.db import transaction as db_transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from communities.models import CommunityMember
from core.models import Follow
from core.pagination import StandardPagination
from posts.models import Post
from tasks.models import UserTask
from users.models import User as UserProfile
from users.serializers import UserProfileSerializer
from wallets.models import Transaction, Wallet


def _annotate_is_following(users, auth_user):
    """Add is_following field to a list of serialized users based on current auth user."""
    if not auth_user or not auth_user.is_authenticated:
        return [dict(u, is_following=False) for u in users]
    try:
        me = UserProfile.objects.get(user_id=auth_user)
        following_ids = set(
            Follow.objects.filter(follower_id=me.id).values_list("following_id", flat=True)
        )
        return [dict(u, is_following=str(u["id"]) in {str(i) for i in following_ids}) for u in users]
    except UserProfile.DoesNotExist:
        return [dict(u, is_following=False) for u in users]


class UserSuggestionsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = min(int(request.query_params.get("limit", 30)), 100)
        queryset = UserProfile.objects.all().order_by("-reputation", "-created_at")

        if request.user.is_authenticated:
            try:
                me = UserProfile.objects.get(user_id=request.user)
                # Exclude self and already-followed users for better suggestions
                following_ids = Follow.objects.filter(follower_id=me.id).values_list("following_id", flat=True)
                queryset = queryset.exclude(user_id=request.user)
            except UserProfile.DoesNotExist:
                pass

        users = UserProfileSerializer(queryset[:limit], many=True).data
        return Response(_annotate_is_following(users, request.user))


class UserSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("query") or request.query_params.get("q") or request.query_params.get("username")
        if not query:
            return Response([])

        limit = min(int(request.query_params.get("limit", 20)), 100)
        users = UserProfile.objects.filter(
            Q(username__icontains=query) | Q(display_name__icontains=query)
        ).order_by("-reputation", "username")[:limit]

        data = UserProfileSerializer(users, many=True).data
        return Response(_annotate_is_following(data, request.user))


class UserSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "notifications_enabled": profile.notifications_enabled,
                "privacy_level": profile.privacy_level,
                "email_updates": profile.email_updates,
            }
        )

    def patch(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        allowed = ["notifications_enabled", "privacy_level", "email_updates"]
        updated_fields = []

        for field in allowed:
            if field in request.data:
                setattr(profile, field, request.data[field])
                updated_fields.append(field)

        if updated_fields:
            updated_fields.append("updated_at")
            profile.save(update_fields=updated_fields)

        return Response(
            {
                "notifications_enabled": profile.notifications_enabled,
                "privacy_level": profile.privacy_level,
                "email_updates": profile.email_updates,
            }
        )


class UserEarningsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            wallet = Wallet.objects.get(user_id=profile)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

        queryset = Transaction.objects.filter(wallet_id=wallet).order_by("-created_at")

        from_date = request.query_params.get("from")
        to_date = request.query_params.get("to")
        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)

        data = [
            {
                "id": str(item.id),
                "transaction_type": item.transaction_type,
                "amount": str(item.amount),
                "currency": item.currency,
                "description": item.description,
                "created_at": item.created_at,
            }
            for item in page
        ]

        summary = queryset.aggregate(total_amount=Sum("amount"))
        response = paginator.get_paginated_response(data)
        response.data["summary"] = {
            "total_amount": str(summary.get("total_amount") or 0),
            "wallet_points": wallet.httn_points,
            "wallet_tokens": str(wallet.httn_tokens),
            "wallet_espees": str(wallet.espees),
        }
        return response


class UserAnalyticsEngagementSeriesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        range_value = request.query_params.get("range", "7d")
        days = 30 if range_value == "30d" else 7
        today = timezone.now().date()
        start_date = today - timedelta(days=days - 1)

        series = []
        for offset in range(days):
            day = start_date + timedelta(days=offset)
            day_posts = Post.objects.filter(author_id=profile, created_at__date=day)
            aggregates = day_posts.aggregate(
                likes_received=Sum("likes_count"),
                comments_received=Sum("comments_count"),
                shares_received=Sum("shares_count"),
            )
            series.append(
                {
                    "date": day.isoformat(),
                    "posts_count": day_posts.count(),
                    "likes_received": int(aggregates.get("likes_received") or 0),
                    "comments_received": int(aggregates.get("comments_received") or 0),
                    "shares_received": int(aggregates.get("shares_received") or 0),
                }
            )

        return Response({"range": range_value, "data": series})


class UserAnalyticsAudienceBreakdownView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        followers_rel = Follow.objects.filter(following_id=profile.id)
        following_rel = Follow.objects.filter(follower_id=profile.id)

        follower_ids = list(followers_rel.values_list("follower_id", flat=True))
        followers = UserProfile.objects.filter(id__in=follower_ids)

        tier_breakdown = {
            "free": followers.filter(tier="free").count(),
            "creator": followers.filter(tier="creator").count(),
            "premium": followers.filter(tier="premium").count(),
        }

        return Response(
            {
                "followers_count": followers_rel.count(),
                "following_count": following_rel.count(),
                "tier_breakdown": tier_breakdown,
            }
        )


class UserStatsByIdView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            profile = UserProfile.objects.get(id=pk)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        posts_count = Post.objects.filter(author_id=profile).count()
        followers_count = Follow.objects.filter(following_id=profile.id).count()
        following_count = Follow.objects.filter(follower_id=profile.id).count()

        return Response(
            {
                "posts_count": posts_count,
                "followers_count": followers_count,
                "following_count": following_count,
                "reputation": profile.reputation,
            }
        )


class UserMeCommunitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        memberships = CommunityMember.objects.filter(user=profile).select_related("community").order_by("-joined_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(memberships, request)

        data = [
            {
                "id": str(item.community.id),
                "name": item.community.name,
                "description": item.community.description,
                "category": item.community.category,
                "image_url": item.community.image_url,
                "member_count": item.community.member_count,
                "is_private": item.community.is_private,
                "created_by": str(item.community.created_by_id),
            }
            for item in page
        ]

        return paginator.get_paginated_response(data)


class UserTaskClaimMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, task_id):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            user_task = UserTask.objects.select_related("task").get(id=task_id, user=profile)
            wallet = Wallet.objects.get(user_id=profile)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except UserTask.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

        if not user_task.completed:
            return Response({"error": "Task not completed yet"}, status=status.HTTP_400_BAD_REQUEST)

        if user_task.claimed:
            return Response({"error": "Reward already claimed"}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            wallet.httn_points += user_task.task.reward
            wallet.save(update_fields=["httn_points", "updated_at"])
            user_task.claimed = True
            user_task.save(update_fields=["claimed"])

        return Response(
            {
                "success": True,
                "reward": user_task.task.reward,
                "new_balance": wallet.httn_points,
            }
        )


class UserInterestsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        interests = request.data.get("interests", [])
        if not isinstance(interests, list):
            return Response({"error": "interests must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        profile.interests = interests
        profile.save(update_fields=["interests", "updated_at"])
        return Response({"success": True, "interests": profile.interests})


class UserBulkFollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        target_ids = request.data.get("user_ids", [])
        if not isinstance(target_ids, list):
            return Response({"error": "user_ids must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        followed = 0
        for user_id in target_ids:
            try:
                target = UserProfile.objects.get(id=user_id)
            except UserProfile.DoesNotExist:
                continue

            if target.id == profile.id:
                continue

            rel, created = Follow.objects.get_or_create(follower_id=profile.id, following_id=target.id)
            if created:
                followed += 1

        return Response({"success": True, "followed": followed})


class UserOnboardingCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        profile.onboarding_completed = True
        profile.save(update_fields=["onboarding_completed", "updated_at"])
        return Response({"success": True})
