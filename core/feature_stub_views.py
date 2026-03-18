import uuid
from datetime import timedelta

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class ConversationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response([])


class ConversationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        return Response([])


class MessageCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        recipient_id = request.data.get("recipient_id")
        content = request.data.get("content")
        if not recipient_id or not content:
            return Response({"error": "recipient_id and content are required"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "id": str(uuid.uuid4()),
                "recipient_id": recipient_id,
                "content": content,
                "read": False,
                "created_at": timezone.now(),
            },
            status=status.HTTP_201_CREATED,
        )


class MessageReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, message_id):
        return Response({"success": True, "id": str(message_id), "read": True})


class MessageUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"unread_count": 0})


class MediaUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        media = request.FILES.get("file") or request.FILES.get("media")
        if not media:
            return Response({"error": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "url": f"/media/{media.name}",
                "name": media.name,
                "size": media.size,
                "content_type": getattr(media, "content_type", None),
            },
            status=status.HTTP_201_CREATED,
        )


class ScheduledPostsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        run_at = request.data.get("run_at") or (timezone.now() + timedelta(hours=1)).isoformat()
        return Response(
            {
                "id": str(uuid.uuid4()),
                "content": request.data.get("content", ""),
                "media_url": request.data.get("media_url"),
                "run_at": run_at,
                "status": "scheduled",
            },
            status=status.HTTP_201_CREATED,
        )


class ScheduledPostsMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response([])


class AiPostingSuggestionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response(
            {
                "suggestions": [
                    {"day": "Mon", "hour": "09:00"},
                    {"day": "Wed", "hour": "13:00"},
                    {"day": "Fri", "hour": "18:00"},
                ]
            }
        )


class StreamChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, stream_id):
        return Response([])

    def post(self, request, stream_id):
        message = request.data.get("message")
        if not message:
            return Response({"error": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "id": str(uuid.uuid4()),
                "stream_id": str(stream_id),
                "message": message,
                "created_at": timezone.now(),
            },
            status=status.HTTP_201_CREATED,
        )


class StreamDonationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, stream_id):
        return Response([])

    def post(self, request, stream_id):
        amount = request.data.get("amount")
        if amount is None:
            return Response({"error": "amount is required"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "id": str(uuid.uuid4()),
                "stream_id": str(stream_id),
                "amount": amount,
                "currency": request.data.get("currency", "espees"),
                "created_at": timezone.now(),
            },
            status=status.HTTP_201_CREATED,
        )


class StreamViewerJoinLeaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, stream_id):
        return Response({"success": True, "stream_id": str(stream_id)})


class AiContentInsightsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        content = request.data.get("content", "")
        words = [w for w in content.strip().split(" ") if w]
        return Response(
            {
                "word_count": len(words),
                "estimated_read_time_sec": max(5, len(words) // 3),
                "sentiment": "neutral",
                "suggestions": ["Add a stronger call to action", "Use one concise hashtag"],
            }
        )
