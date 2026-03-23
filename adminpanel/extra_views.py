from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination
from users.models import User as UserProfile

from .models import AdCampaign


def _serialize_campaign(item):
    return {
        "id": str(item.id),
        "title": item.title,
        "description": item.description,
        "image_url": item.image_url,
        "cta_text": item.cta_text or "Learn More",
        "target_url": item.target_url,
        "sponsor_name": item.sponsor_name or item.user.username if hasattr(item, 'user') else None,
        "reward_points": item.reward_points,
        "is_featured": item.is_featured,
        "budget_points": item.budget_points,
        "spent_points": item.spent_points,
        "impressions": item.impressions,
        "clicks": item.clicks,
        "status": item.status,
        "start_date": item.start_date,
        "end_date": item.end_date,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


class AdminRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            "is_admin": bool(request.user.is_staff),
            "role": "admin" if request.user.is_staff else "user",
        })


class AdminVerifyUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        try:
            profile = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        profile.is_verified = True
        profile.save(update_fields=["is_verified", "updated_at"])
        return Response({"success": True, "user_id": str(profile.id), "is_verified": True})


# ── Public: active ads for display in the app ──────────────────────────────
class PublicActiveAdsView(APIView):
    """Returns currently active ad campaigns for display — no auth required."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 10)), 20)
        from django.utils import timezone
        today = timezone.now().date()
        ads = (
            AdCampaign.objects
            .select_related('user')
            .filter(status='active')
            .filter(
                models.Q(start_date__isnull=True) | models.Q(start_date__lte=today)
            )
            .filter(
                models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
            )
            .order_by('-is_featured', '-created_at')[:limit]
        )
        return Response([_serialize_campaign(a) for a in ads])

    def post(self, request, campaign_id=None):
        """Track a click on an ad."""
        if not campaign_id:
            return Response({"error": "campaign_id required"}, status=400)
        try:
            ad = AdCampaign.objects.get(id=campaign_id, status='active')
            ad.clicks += 1
            ad.save(update_fields=['clicks'])
            return Response({"success": True})
        except AdCampaign.DoesNotExist:
            return Response({"error": "Ad not found"}, status=404)


# ── Admin: full CRUD for all campaigns ────────────────────────────────────
class AdminAdCampaignListView(APIView):
    """Admin-only: list all campaigns and create new ones."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = AdCampaign.objects.select_related('user').order_by('-created_at')
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response([_serialize_campaign(a) for a in page])

    def post(self, request):
        data = request.data
        title = data.get("title")
        if not title:
            return Response({"error": "title is required"}, status=400)

        # Allow admin to assign to any user or default to themselves
        user_id = data.get("user_id")
        if user_id:
            try:
                profile = UserProfile.objects.get(id=user_id)
            except UserProfile.DoesNotExist:
                return Response({"error": "User not found"}, status=404)
        else:
            try:
                profile = UserProfile.objects.get(user_id=request.user)
            except UserProfile.DoesNotExist:
                return Response({"error": "Admin profile not found"}, status=404)

        campaign = AdCampaign.objects.create(
            user=profile,
            title=title,
            description=data.get("description"),
            image_url=data.get("image_url"),
            cta_text=data.get("cta_text", "Learn More"),
            target_url=data.get("target_url"),
            sponsor_name=data.get("sponsor_name"),
            reward_points=int(data.get("reward_points", 5) or 5),
            is_featured=bool(data.get("is_featured", False)),
            budget_points=int(data.get("budget_points", 0) or 0),
            status=data.get("status", "active"),
            start_date=data.get("start_date") or None,
            end_date=data.get("end_date") or None,
        )
        return Response(_serialize_campaign(campaign), status=201)


class AdminAdCampaignDetailView(APIView):
    """Admin-only: get/update/delete a specific campaign."""
    permission_classes = [permissions.IsAdminUser]

    def _get_campaign(self, campaign_id):
        try:
            return AdCampaign.objects.select_related('user').get(id=campaign_id)
        except AdCampaign.DoesNotExist:
            return None

    def get(self, request, campaign_id):
        ad = self._get_campaign(campaign_id)
        if not ad:
            return Response({"error": "Campaign not found"}, status=404)
        return Response(_serialize_campaign(ad))

    def patch(self, request, campaign_id):
        ad = self._get_campaign(campaign_id)
        if not ad:
            return Response({"error": "Campaign not found"}, status=404)

        allowed = [
            "title", "description", "image_url", "cta_text", "target_url",
            "sponsor_name", "reward_points", "is_featured",
            "budget_points", "status", "start_date", "end_date",
        ]
        updated = [f for f in allowed if f in request.data]
        for field in updated:
            setattr(ad, field, request.data[field])
        if updated:
            ad.save(update_fields=updated + ['updated_at'])
        return Response(_serialize_campaign(ad))

    def delete(self, request, campaign_id):
        ad = self._get_campaign(campaign_id)
        if not ad:
            return Response({"error": "Campaign not found"}, status=404)
        ad.delete()
        return Response({"success": True})


# ── User-facing: own campaigns CRUD (unchanged behaviour) ─────────────────
class AdCampaignListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=404)

        queryset = AdCampaign.objects.filter(user=profile).order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response([_serialize_campaign(a) for a in page])

    def post(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=404)

        title = request.data.get("title")
        if not title:
            return Response({"error": "title is required"}, status=400)

        campaign = AdCampaign.objects.create(
            user=profile,
            title=title,
            description=request.data.get("description"),
            image_url=request.data.get("image_url"),
            cta_text=request.data.get("cta_text", "Learn More"),
            target_url=request.data.get("target_url"),
            sponsor_name=request.data.get("sponsor_name"),
            reward_points=int(request.data.get("reward_points", 5) or 5),
            is_featured=bool(request.data.get("is_featured", False)),
            budget_points=int(request.data.get("budget_points", 0) or 0),
            status=request.data.get("status", "active"),
            start_date=request.data.get("start_date") or None,
            end_date=request.data.get("end_date") or None,
        )
        return Response(_serialize_campaign(campaign), status=201)


class AdCampaignDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, campaign_id):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            campaign = AdCampaign.objects.get(id=campaign_id, user=profile)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=404)
        except AdCampaign.DoesNotExist:
            return Response({"error": "Campaign not found"}, status=404)

        allowed = [
            "title", "description", "image_url", "cta_text", "target_url",
            "sponsor_name", "reward_points", "budget_points", "status",
            "start_date", "end_date",
        ]
        updated = [f for f in allowed if f in request.data]
        for field in updated:
            setattr(campaign, field, request.data[field])
        if updated:
            campaign.save(update_fields=updated + ['updated_at'])
        return Response(_serialize_campaign(campaign))

    def delete(self, request, campaign_id):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            campaign = AdCampaign.objects.get(id=campaign_id, user=profile)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=404)
        except AdCampaign.DoesNotExist:
            return Response({"error": "Campaign not found"}, status=404)

        campaign.delete()
        return Response({"success": True})


# needed for Q import
from django.db import models
