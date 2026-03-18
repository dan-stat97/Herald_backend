from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination
from users.models import User as UserProfile

from .models import AdCampaign


class AdminRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "is_admin": bool(request.user.is_staff),
                "role": "admin" if request.user.is_staff else "user",
            }
        )


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


class AdCampaignListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        queryset = AdCampaign.objects.filter(user=profile).order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = [
            {
                "id": str(item.id),
                "title": item.title,
                "description": item.description,
                "budget_points": item.budget_points,
                "spent_points": item.spent_points,
                "impressions": item.impressions,
                "clicks": item.clicks,
                "status": item.status,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "created_at": item.created_at,
            }
            for item in page
        ]
        return paginator.get_paginated_response(data)

    def post(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        title = request.data.get("title")
        if not title:
            return Response({"error": "title is required"}, status=status.HTTP_400_BAD_REQUEST)

        campaign = AdCampaign.objects.create(
            user=profile,
            title=title,
            description=request.data.get("description"),
            budget_points=int(request.data.get("budget_points", 0) or 0),
            spent_points=int(request.data.get("spent_points", 0) or 0),
            impressions=int(request.data.get("impressions", 0) or 0),
            clicks=int(request.data.get("clicks", 0) or 0),
            status=request.data.get("status", "active"),
            start_date=request.data.get("start_date") or None,
            end_date=request.data.get("end_date") or None,
        )

        return Response(
            {
                "id": str(campaign.id),
                "title": campaign.title,
                "description": campaign.description,
                "budget_points": campaign.budget_points,
                "spent_points": campaign.spent_points,
                "impressions": campaign.impressions,
                "clicks": campaign.clicks,
                "status": campaign.status,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "created_at": campaign.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class AdCampaignDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, campaign_id):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            campaign = AdCampaign.objects.get(id=campaign_id, user=profile)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except AdCampaign.DoesNotExist:
            return Response({"error": "Campaign not found"}, status=status.HTTP_404_NOT_FOUND)

        allowed_fields = [
            "title",
            "description",
            "budget_points",
            "spent_points",
            "impressions",
            "clicks",
            "status",
            "start_date",
            "end_date",
        ]

        updated = []
        for field in allowed_fields:
            if field in request.data:
                setattr(campaign, field, request.data[field])
                updated.append(field)

        if updated:
            campaign.save(update_fields=updated)

        return Response({"success": True})

    def delete(self, request, campaign_id):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            campaign = AdCampaign.objects.get(id=campaign_id, user=profile)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except AdCampaign.DoesNotExist:
            return Response({"error": "Campaign not found"}, status=status.HTTP_404_NOT_FOUND)

        campaign.delete()
        return Response({"success": True})
