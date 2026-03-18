from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction as db_transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination
from livestreams.models import LiveStream, StreamChatMessage, StreamDonation, StreamViewerEvent
from posts.models import ScheduledPost
from users.models import DirectMessage, User as UserProfile
from wallets.models import Transaction, Wallet


class ConversationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        limit = min(int(request.query_params.get("limit", 50)), 100)

        messages = DirectMessage.objects.filter(Q(sender=profile) | Q(recipient=profile)).select_related("sender", "recipient").order_by("-created_at")
        unread_map = {
            str(item["sender"]): item["count"]
            for item in DirectMessage.objects.filter(recipient=profile, read=False)
            .values("sender")
            .annotate(count=Count("id"))
        }

        conversations = []
        seen = set()
        for msg in messages:
            peer = msg.recipient if msg.sender_id == profile.id else msg.sender
            peer_key = str(peer.id)
            if peer_key in seen:
                continue
            seen.add(peer_key)
            conversations.append(
                {
                    "user": {
                        "id": str(peer.id),
                        "username": peer.username,
                        "display_name": peer.display_name,
                        "avatar_url": peer.avatar_url,
                    },
                    "last_message": msg.content,
                    "last_message_at": msg.created_at,
                    "unread_count": unread_map.get(peer_key, 0),
                }
            )
            if len(conversations) >= limit:
                break

        return Response(conversations)


class ConversationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        other_user = get_object_or_404(UserProfile, id=user_id)

        queryset = DirectMessage.objects.filter(
            (Q(sender=profile) & Q(recipient=other_user)) | (Q(sender=other_user) & Q(recipient=profile))
        ).select_related("sender", "recipient").order_by("-created_at")

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = [
            {
                "id": str(item.id),
                "sender_id": str(item.sender_id),
                "recipient_id": str(item.recipient_id),
                "content": item.content,
                "read": item.read,
                "created_at": item.created_at,
            }
            for item in page
        ]
        return paginator.get_paginated_response(data)


class MessageCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        sender = get_object_or_404(UserProfile, user_id=request.user)
        recipient_id = request.data.get("recipient_id")
        content = (request.data.get("content") or "").strip()

        if not recipient_id or not content:
            return Response({"error": "recipient_id and content are required"}, status=status.HTTP_400_BAD_REQUEST)

        recipient = get_object_or_404(UserProfile, id=recipient_id)
        if sender.id == recipient.id:
            return Response({"error": "Cannot message yourself"}, status=status.HTTP_400_BAD_REQUEST)

        msg = DirectMessage.objects.create(sender=sender, recipient=recipient, content=content)
        return Response(
            {
                "id": str(msg.id),
                "sender_id": str(msg.sender_id),
                "recipient_id": str(msg.recipient_id),
                "content": msg.content,
                "read": msg.read,
                "created_at": msg.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class MessageReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, message_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        msg = get_object_or_404(DirectMessage, id=message_id, recipient=profile)
        if not msg.read:
            msg.read = True
            msg.save(update_fields=["read"])
        return Response({"success": True, "id": str(msg.id), "read": msg.read})


class MessageUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        unread_count = DirectMessage.objects.filter(recipient=profile, read=False).count()
        return Response({"unread_count": unread_count})


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
        profile = get_object_or_404(UserProfile, user_id=request.user)
        content = request.data.get("content", "")
        media_url = request.data.get("media_url")
        media_type = request.data.get("media_type")
        run_at_raw = request.data.get("run_at")

        if run_at_raw:
            run_at = parse_datetime(run_at_raw)
            if run_at is None:
                return Response({"error": "Invalid run_at datetime"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            run_at = timezone.now() + timedelta(hours=1)

        scheduled = ScheduledPost.objects.create(
            user=profile,
            content=content,
            media_url=media_url,
            media_type=media_type,
            run_at=run_at,
        )

        return Response(
            {
                "id": str(scheduled.id),
                "content": scheduled.content,
                "media_url": scheduled.media_url,
                "media_type": scheduled.media_type,
                "run_at": scheduled.run_at,
                "status": scheduled.status,
            },
            status=status.HTTP_201_CREATED,
        )


class ScheduledPostsMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        queryset = ScheduledPost.objects.filter(user=profile).order_by("run_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = [
            {
                "id": str(item.id),
                "content": item.content,
                "media_url": item.media_url,
                "media_type": item.media_type,
                "run_at": item.run_at,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in page
        ]
        return paginator.get_paginated_response(data)


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
        stream = get_object_or_404(LiveStream, id=stream_id)
        queryset = StreamChatMessage.objects.filter(stream=stream).select_related("user").order_by("-created_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = [
            {
                "id": str(item.id),
                "stream_id": str(stream.id),
                "user": {
                    "id": str(item.user.id),
                    "username": item.user.username,
                    "display_name": item.user.display_name,
                    "avatar_url": item.user.avatar_url,
                },
                "message": item.message,
                "created_at": item.created_at,
            }
            for item in page
        ]
        return paginator.get_paginated_response(data)

    def post(self, request, stream_id):
        stream = get_object_or_404(LiveStream, id=stream_id)
        profile = get_object_or_404(UserProfile, user_id=request.user)
        message = (request.data.get("message") or "").strip()
        if not message:
            return Response({"error": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

        item = StreamChatMessage.objects.create(stream=stream, user=profile, message=message)
        return Response(
            {
                "id": str(item.id),
                "stream_id": str(stream.id),
                "user": {
                    "id": str(profile.id),
                    "username": profile.username,
                    "display_name": profile.display_name,
                    "avatar_url": profile.avatar_url,
                },
                "message": item.message,
                "created_at": item.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class StreamDonationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, stream_id):
        stream = get_object_or_404(LiveStream, id=stream_id)
        queryset = StreamDonation.objects.filter(stream=stream).select_related("user").order_by("-created_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = [
            {
                "id": str(item.id),
                "stream_id": str(stream.id),
                "user": {
                    "id": str(item.user.id),
                    "username": item.user.username,
                    "display_name": item.user.display_name,
                },
                "amount": str(item.amount),
                "currency": item.currency,
                "message": item.message,
                "created_at": item.created_at,
            }
            for item in page
        ]
        return paginator.get_paginated_response(data)

    def post(self, request, stream_id):
        stream = get_object_or_404(LiveStream, id=stream_id)
        profile = get_object_or_404(UserProfile, user_id=request.user)

        amount_raw = request.data.get("amount")
        currency = request.data.get("currency", "espees")
        message = request.data.get("message")

        if amount_raw is None:
            return Response({"error": "amount is required"}, status=status.HTTP_400_BAD_REQUEST)
        if currency not in {"points", "tokens", "espees"}:
            return Response({"error": "Unsupported currency"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(amount_raw))
        except (InvalidOperation, TypeError, ValueError):
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "amount must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)

        if currency == "points" and amount != int(amount):
            return Response({"error": "points donation must be a whole number"}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            sender_wallet = get_object_or_404(Wallet.objects.select_for_update(), user_id=profile)
            host_wallet, _ = Wallet.objects.select_for_update().get_or_create(user_id=stream.user)

            if currency == "points":
                points_amount = int(amount)
                if sender_wallet.httn_points < points_amount:
                    return Response({"error": "Insufficient points balance"}, status=status.HTTP_400_BAD_REQUEST)
                sender_wallet.httn_points -= points_amount
                host_wallet.httn_points += points_amount
                sender_wallet.save(update_fields=["httn_points", "updated_at"])
                host_wallet.save(update_fields=["httn_points", "updated_at"])
            elif currency == "tokens":
                if sender_wallet.httn_tokens < amount:
                    return Response({"error": "Insufficient token balance"}, status=status.HTTP_400_BAD_REQUEST)
                sender_wallet.httn_tokens -= amount
                host_wallet.httn_tokens += amount
                sender_wallet.save(update_fields=["httn_tokens", "updated_at"])
                host_wallet.save(update_fields=["httn_tokens", "updated_at"])
            else:
                if sender_wallet.espees < amount:
                    return Response({"error": "Insufficient espees balance"}, status=status.HTTP_400_BAD_REQUEST)
                sender_wallet.espees -= amount
                host_wallet.espees += amount
                sender_wallet.save(update_fields=["espees", "updated_at"])
                host_wallet.save(update_fields=["espees", "updated_at"])

            donation = StreamDonation.objects.create(
                stream=stream,
                user=profile,
                amount=amount,
                currency=currency,
                message=message,
            )

            Transaction.objects.create(
                wallet_id=sender_wallet,
                transaction_type='transfer',
                amount=amount,
                currency=currency,
                description=f'Donated to stream {stream.id}',
            )
            Transaction.objects.create(
                wallet_id=host_wallet,
                transaction_type='deposit',
                amount=amount,
                currency=currency,
                description=f'Received stream donation from {profile.username}',
            )

        return Response(
            {
                "id": str(donation.id),
                "stream_id": str(stream.id),
                "amount": str(donation.amount),
                "currency": donation.currency,
                "message": donation.message,
                "created_at": donation.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class StreamViewerJoinLeaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, stream_id):
        stream = get_object_or_404(LiveStream, id=stream_id)
        profile = get_object_or_404(UserProfile, user_id=request.user)

        event_type = request.data.get("event_type")
        if event_type not in {"join", "leave"}:
            event_type = "leave" if "viewer-leave" in request.path else "join"

        StreamViewerEvent.objects.create(stream=stream, user=profile, event_type=event_type)

        if event_type == "join":
            stream.viewer_count = (stream.viewer_count or 0) + 1
        else:
            stream.viewer_count = max(0, (stream.viewer_count or 0) - 1)
        stream.save(update_fields=["viewer_count"])

        return Response({"success": True, "stream_id": str(stream.id), "event_type": event_type, "viewer_count": stream.viewer_count})


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
