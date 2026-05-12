from datetime import timedelta
from decimal import Decimal, InvalidOperation
import json
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.db import transaction as db_transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination
from core.models import Follow
from livestreams.models import LiveStream, StreamChatMessage, StreamDonation, StreamViewerEvent
from notifications.models import Notification
from posts.models import ScheduledPost
from users.legacy_profiles import get_legacy_profile_for_user_profile
from users.models import CallSession, DevicePushToken, DirectMessage, PinnedConversation, User as UserProfile
from wallets.models import Transaction, Wallet


def _conversation_queryset(profile, other_user=None):
    queryset = DirectMessage.objects.filter(Q(sender=profile) | Q(recipient=profile))
    if other_user is not None:
        queryset = queryset.filter(
            (Q(sender=profile) & Q(recipient=other_user)) | (Q(sender=other_user) & Q(recipient=profile))
        )
    queryset = queryset.exclude(deleted_for_everyone_at__isnull=False)
    queryset = queryset.exclude(Q(sender=profile) & Q(deleted_for_sender=True))
    queryset = queryset.exclude(Q(recipient=profile) & Q(deleted_for_recipient=True))
    return queryset.select_related(
        "sender",
        "recipient",
        "reply_to",
        "reply_to__sender",
        "reply_to__recipient",
        "forwarded_from",
        "forwarded_from__sender",
    )


def _serialize_attachment(attachment):
    if not isinstance(attachment, dict):
        return None
    return {
        "url": attachment.get("url"),
        "type": attachment.get("type") or "file",
        "name": attachment.get("name"),
        "size": attachment.get("size"),
        "mime_type": attachment.get("mime_type"),
        "thumbnail_url": attachment.get("thumbnail_url"),
    }


def _serialize_message(item, viewer, viewer_allows_receipts=None):
    if viewer_allows_receipts is None:
        viewer_allows_receipts = viewer.show_read_receipts
    visible_attachments = [
        serialized
        for serialized in (_serialize_attachment(attachment) for attachment in (item.attachments or []))
        if serialized
    ]
    reply_to = None
    if item.reply_to_id and item.reply_to and item.reply_to.deleted_for_everyone_at is None:
        reply_to = {
            "id": str(item.reply_to.id),
            "sender_id": str(item.reply_to.sender_id),
            "sender_name": item.reply_to.sender.display_name or item.reply_to.sender.username,
            "content": item.reply_to.content,
            "kind": item.reply_to.kind,
        }
    forwarded_from = None
    if item.forwarded_from_id and item.forwarded_from:
        forwarded_from = {
            "id": str(item.forwarded_from.id),
            "sender_name": item.forwarded_from.sender.display_name or item.forwarded_from.sender.username,
            "kind": item.forwarded_from.kind,
        }
    return {
        "id": str(item.id),
        "sender_id": str(item.sender_id),
        "recipient_id": str(item.recipient_id),
        "content": item.content,
        "kind": item.kind,
        "attachments": visible_attachments,
        "reply_to": reply_to,
        "forwarded_from": forwarded_from,
        "reactions": item.reactions or [],
        "metadata": item.metadata or {},
        "read": (
            item.read
            if item.recipient_id == viewer.id
            else bool(item.read and viewer_allows_receipts and item.recipient.show_read_receipts)
        ),
        "read_at": item.read_at,
        "edited_at": item.edited_at,
        "created_at": item.created_at,
    }


def _serialize_call_session(call_session, viewer):
    is_caller = call_session.caller_id == viewer.id
    other_user = call_session.callee if is_caller else call_session.caller
    return {
        "id": str(call_session.id),
        "mode": call_session.mode,
        "status": call_session.status,
        "room_name": call_session.room_name,
        "room_url": call_session.room_url,
        "is_caller": is_caller,
        "muted": call_session.caller_muted if is_caller else call_session.callee_muted,
        "video_enabled": call_session.caller_video_enabled if is_caller else call_session.callee_video_enabled,
        "started_at": call_session.started_at,
        "responded_at": call_session.responded_at,
        "ended_at": call_session.ended_at,
        "created_at": call_session.created_at,
        "peer": {
            "id": str(other_user.id),
            "username": other_user.username,
            "display_name": other_user.display_name,
            "avatar_url": other_user.avatar_url,
        },
    }


def _build_jitsi_url(room_name, mode, muted=False, video_enabled=True):
    params = ["config.prejoinConfig.enabled=true"]
    if mode == "audio":
        params.append("config.startAudioOnly=true")
        params.append("config.startWithVideoMuted=true")
    else:
        params.append(f"config.startWithVideoMuted={'false' if video_enabled else 'true'}")
    if muted:
        params.append("config.startWithAudioMuted=true")
    return f"https://meet.jit.si/{room_name}#{'&'.join(params)}"


def _send_expo_push(token, title, body, data):
    payload = {
        "to": token,
        "title": title,
        "body": body,
        "sound": "default",
        "priority": "high",
        "data": data,
    }
    request = urllib_request.Request(
        "https://exp.host/--/api/v2/push/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=8) as response:
            return response.read().decode("utf-8")
    except urllib_error.URLError:
        return None


class ConversationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        limit = min(int(request.query_params.get("limit", 50)), 100)
        pinned_peer_ids = list(
            PinnedConversation.objects.filter(owner=profile)
            .order_by("created_at")
            .values_list("peer_id", flat=True)
        )

        messages = _conversation_queryset(profile).order_by("-created_at")
        unread_map = {
            str(item["sender"]): item["count"]
            for item in DirectMessage.objects.filter(recipient=profile, read=False, deleted_for_everyone_at__isnull=True)
            .values("sender")
            .annotate(count=Count("id"))
        }

        conversations_by_peer = {}
        seen = set()
        for msg in messages:
            peer = msg.recipient if msg.sender_id == profile.id else msg.sender
            peer_key = str(peer.id)
            if peer_key in seen:
                continue
            seen.add(peer_key)
            conversations_by_peer[peer_key] = {
                "user": {
                    "id": str(peer.id),
                    "username": peer.username,
                    "display_name": peer.display_name,
                    "avatar_url": peer.avatar_url,
                    "created_at": peer.created_at,
                },
                "last_message": msg.content or (
                    f"{msg.kind.replace('_', ' ').title()}" if msg.kind != "text" else ""
                ),
                "last_message_at": msg.created_at,
                "last_message_kind": msg.kind,
                "unread_count": unread_map.get(peer_key, 0),
                "pinned": peer.id in pinned_peer_ids,
            }

        ordered = []
        for peer_id in pinned_peer_ids:
            key = str(peer_id)
            if key in conversations_by_peer:
                ordered.append(conversations_by_peer[key])
        remaining = [
            convo
            for key, convo in conversations_by_peer.items()
            if key not in {str(peer_id) for peer_id in pinned_peer_ids}
        ]
        remaining.sort(key=lambda convo: convo["last_message_at"], reverse=True)
        ordered.extend(remaining)
        return Response(ordered[:limit])


class ConversationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        other_user = get_object_or_404(UserProfile, id=user_id)

        queryset = _conversation_queryset(profile, other_user=other_user).order_by("-created_at")

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        viewer_allows_receipts = profile.show_read_receipts
        data = [_serialize_message(item, profile, viewer_allows_receipts) for item in page]
        response = paginator.get_paginated_response(data)
        response.data["peer"] = {
            "id": str(other_user.id),
            "username": other_user.username,
            "display_name": other_user.display_name,
            "avatar_url": other_user.avatar_url,
            "bio": other_user.bio,
            "created_at": other_user.created_at,
            "allow_message_requests": other_user.allow_message_requests,
            "show_read_receipts": other_user.show_read_receipts,
            "is_pinned": PinnedConversation.objects.filter(owner=profile, peer=other_user).exists(),
        }
        return response


class MessageCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        sender = get_object_or_404(UserProfile, user_id=request.user)
        recipient_id = request.data.get("recipient_id")
        content = (request.data.get("content") or "").strip()
        kind = (request.data.get("kind") or "text").strip() or "text"
        attachments = request.data.get("attachments") or []
        metadata = request.data.get("metadata") or {}
        reply_to_id = request.data.get("reply_to_id")
        forwarded_from_id = request.data.get("forwarded_from_id")

        if not recipient_id:
            return Response({"error": "recipient_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not content and not attachments and kind == "text":
            return Response({"error": "content is required"}, status=status.HTTP_400_BAD_REQUEST)

        recipient = get_object_or_404(UserProfile, id=recipient_id)
        if sender.id == recipient.id:
            return Response({"error": "Cannot message yourself"}, status=status.HTTP_400_BAD_REQUEST)

        prior_conversation_exists = DirectMessage.objects.filter(
            (Q(sender=sender) & Q(recipient=recipient)) | (Q(sender=recipient) & Q(recipient=sender))
        ).exists()

        recipient_follows_sender = False
        sender_legacy = get_legacy_profile_for_user_profile(sender)
        recipient_legacy = get_legacy_profile_for_user_profile(recipient)
        if sender_legacy and recipient_legacy:
            recipient_follows_sender = Follow.objects.filter(
                follower_id=recipient_legacy.id,
                following_id=sender_legacy.id,
            ).exists()

        if (
            not recipient.allow_message_requests
            and not prior_conversation_exists
            and not recipient_follows_sender
        ):
            return Response(
                {
                    "error": "This user only accepts message requests from accounts they follow.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        reply_to = None
        if reply_to_id:
            reply_to = get_object_or_404(DirectMessage, id=reply_to_id)
        forwarded_from = None
        if forwarded_from_id:
            forwarded_from = get_object_or_404(DirectMessage, id=forwarded_from_id)

        msg = DirectMessage.objects.create(
            sender=sender,
            recipient=recipient,
            content=content,
            kind=kind,
            attachments=attachments if isinstance(attachments, list) else [],
            metadata=metadata if isinstance(metadata, dict) else {},
            reply_to=reply_to,
            forwarded_from=forwarded_from,
        )
        return Response(_serialize_message(msg, sender), status=status.HTTP_201_CREATED)


class MessageReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, message_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        msg = get_object_or_404(DirectMessage, id=message_id, recipient=profile)
        if not msg.read:
            msg.read = True
            msg.read_at = timezone.now()
            msg.save(update_fields=["read", "read_at"])
        return Response({"success": True, "id": str(msg.id), "read": msg.read})


class MessageUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, message_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        msg = get_object_or_404(DirectMessage, id=message_id, sender=profile, deleted_for_everyone_at__isnull=True)
        content = (request.data.get("content") or "").strip()
        if not content:
            return Response({"error": "content is required"}, status=status.HTTP_400_BAD_REQUEST)
        msg.content = content
        msg.edited_at = timezone.now()
        msg.save(update_fields=["content", "edited_at"])
        return Response(_serialize_message(msg, profile))


class MessageReactionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, message_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        msg = get_object_or_404(DirectMessage, id=message_id, deleted_for_everyone_at__isnull=True)
        emoji = (request.data.get("emoji") or "").strip()
        if not emoji:
            return Response({"error": "emoji is required"}, status=status.HTTP_400_BAD_REQUEST)
        reactions = [reaction for reaction in (msg.reactions or []) if reaction.get("user_id") != str(profile.id)]
        reactions.append({
            "user_id": str(profile.id),
            "emoji": emoji,
            "created_at": timezone.now().isoformat(),
        })
        msg.reactions = reactions
        msg.save(update_fields=["reactions"])
        return Response({"success": True, "reactions": msg.reactions})

    def delete(self, request, message_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        msg = get_object_or_404(DirectMessage, id=message_id, deleted_for_everyone_at__isnull=True)
        emoji = (request.data.get("emoji") or request.query_params.get("emoji") or "").strip()
        reactions = [
            reaction
            for reaction in (msg.reactions or [])
            if not (
                reaction.get("user_id") == str(profile.id)
                and (not emoji or reaction.get("emoji") == emoji)
            )
        ]
        msg.reactions = reactions
        msg.save(update_fields=["reactions"])
        return Response({"success": True, "reactions": msg.reactions})


class MessageDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, message_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        msg = get_object_or_404(DirectMessage, id=message_id)
        mode = (request.data.get("mode") or "me").strip().lower()

        if mode == "all":
            if msg.sender_id != profile.id:
                return Response({"error": "Only the sender can delete for everyone"}, status=status.HTTP_403_FORBIDDEN)
            msg.deleted_for_everyone_at = timezone.now()
            msg.save(update_fields=["deleted_for_everyone_at"])
            return Response({"success": True, "mode": "all"})

        update_fields = []
        if msg.sender_id == profile.id:
            msg.deleted_for_sender = True
            update_fields.append("deleted_for_sender")
        if msg.recipient_id == profile.id:
            msg.deleted_for_recipient = True
            update_fields.append("deleted_for_recipient")
        if not update_fields:
            return Response({"error": "You cannot delete this message"}, status=status.HTTP_403_FORBIDDEN)
        msg.save(update_fields=update_fields)
        return Response({"success": True, "mode": "me"})


class ConversationPinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        peer = get_object_or_404(UserProfile, id=user_id)
        pin, created = PinnedConversation.objects.get_or_create(owner=profile, peer=peer)
        return Response({"success": True, "pinned": True, "created": created, "id": str(pin.id)})

    def delete(self, request, user_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        peer = get_object_or_404(UserProfile, id=user_id)
        PinnedConversation.objects.filter(owner=profile, peer=peer).delete()
        return Response({"success": True, "pinned": False})


class PushTokenRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        token = (request.data.get("token") or "").strip()
        platform = (request.data.get("platform") or "unknown").strip().lower()
        if not token:
            return Response({"error": "token is required"}, status=status.HTTP_400_BAD_REQUEST)
        if platform not in {"ios", "android", "web", "unknown"}:
            platform = "unknown"
        item, created = DevicePushToken.objects.update_or_create(
            token=token,
            defaults={
                "user": profile,
                "platform": platform,
                "enabled": True,
            },
        )
        return Response({"success": True, "created": created, "id": str(item.id)})


class CallSessionStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        caller = get_object_or_404(UserProfile, user_id=request.user)
        callee = get_object_or_404(UserProfile, id=request.data.get("recipient_id"))
        mode = (request.data.get("mode") or "audio").strip().lower()
        muted = bool(request.data.get("muted", False))
        video_enabled = bool(request.data.get("video_enabled", mode == "video"))
        if mode not in {"audio", "video"}:
            return Response({"error": "mode must be audio or video"}, status=status.HTTP_400_BAD_REQUEST)
        if caller.id == callee.id:
            return Response({"error": "Cannot call yourself"}, status=status.HTTP_400_BAD_REQUEST)

        room_name = f"herald{mode}{str(caller.id).replace('-', '')[:10]}{int(timezone.now().timestamp())}"
        room_url = _build_jitsi_url(room_name, mode, muted=muted, video_enabled=video_enabled)

        with db_transaction.atomic():
            message = DirectMessage.objects.create(
                sender=caller,
                recipient=callee,
                content="Started a voice call" if mode == "audio" else "Started a video call",
                kind="audio_call" if mode == "audio" else "video_call",
                metadata={
                    "status": "ringing",
                    "room": room_name,
                    "call_url": room_url,
                    "mode": f"{mode}_call",
                },
            )
            call_session = CallSession.objects.create(
                caller=caller,
                callee=callee,
                mode=mode,
                room_name=room_name,
                room_url=room_url,
                related_message=message,
                caller_muted=muted,
                caller_video_enabled=video_enabled if mode == "video" else False,
                callee_video_enabled=(mode == "video"),
            )
            Notification.objects.create(
                user_id=callee,
                notification_type="system",
                title="Incoming call",
                message=f"{caller.display_name or caller.username} is calling you",
                related_resource_type="call_session",
                related_resource_id=str(call_session.id),
                actor_id=str(caller.id),
                actor_name=caller.display_name or caller.username,
                actor_avatar=caller.avatar_url,
                actor_verified=caller.is_verified,
            )

        if callee.notifications_enabled and callee.push_notifications:
            for token in DevicePushToken.objects.filter(user=callee, enabled=True).values_list("token", flat=True):
                _send_expo_push(
                    token,
                    "Incoming call",
                    f"{caller.display_name or caller.username} is calling you",
                    {
                        "type": "incoming_call",
                        "call_session_id": str(call_session.id),
                        "room_url": room_url,
                        "mode": mode,
                        "caller_id": str(caller.id),
                        "caller_username": caller.username,
                        "caller_display_name": caller.display_name,
                    },
                )

        return Response(_serialize_call_session(call_session, caller), status=status.HTTP_201_CREATED)


class ActiveCallSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        call_session = (
            CallSession.objects.filter(
                Q(caller=profile) | Q(callee=profile),
                status__in=["ringing", "accepted"],
            )
            .select_related("caller", "callee")
            .order_by("-created_at")
            .first()
        )
        if not call_session:
            return Response({"active_call": None})
        return Response({"active_call": _serialize_call_session(call_session, profile)})


class CallSessionRespondView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, call_session_id, action):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        call_session = get_object_or_404(CallSession.objects.select_related("caller", "callee"), id=call_session_id)
        action = action.strip().lower()
        if action not in {"accept", "decline", "end"}:
            return Response({"error": "Unsupported action"}, status=status.HTTP_400_BAD_REQUEST)

        if action == "accept":
            if call_session.callee_id != profile.id:
                return Response({"error": "Only the callee can accept this call"}, status=status.HTTP_403_FORBIDDEN)
            call_session.status = "accepted"
            call_session.responded_at = timezone.now()
            call_session.started_at = call_session.started_at or timezone.now()
            call_session.save(update_fields=["status", "responded_at", "started_at", "updated_at"])
            if call_session.related_message_id:
                call_session.related_message.metadata = {
                    **(call_session.related_message.metadata or {}),
                    "status": "accepted",
                    "call_session_id": str(call_session.id),
                }
                call_session.related_message.save(update_fields=["metadata"])
        elif action == "decline":
            if call_session.callee_id != profile.id:
                return Response({"error": "Only the callee can decline this call"}, status=status.HTTP_403_FORBIDDEN)
            call_session.status = "declined"
            call_session.responded_at = timezone.now()
            call_session.ended_at = timezone.now()
            call_session.save(update_fields=["status", "responded_at", "ended_at", "updated_at"])
        else:
            if profile.id not in {call_session.caller_id, call_session.callee_id}:
                return Response({"error": "You cannot end this call"}, status=status.HTTP_403_FORBIDDEN)
            call_session.status = "ended" if call_session.status == "accepted" else "canceled"
            call_session.ended_at = timezone.now()
            call_session.save(update_fields=["status", "ended_at", "updated_at"])

        return Response({"success": True, "call_session": _serialize_call_session(call_session, profile)})


class CallSessionControlsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, call_session_id):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        call_session = get_object_or_404(CallSession, id=call_session_id)
        if profile.id not in {call_session.caller_id, call_session.callee_id}:
            return Response({"error": "You cannot update this call"}, status=status.HTTP_403_FORBIDDEN)
        muted = request.data.get("muted")
        video_enabled = request.data.get("video_enabled")
        update_fields = []
        if profile.id == call_session.caller_id:
            if muted is not None:
                call_session.caller_muted = bool(muted)
                update_fields.append("caller_muted")
            if video_enabled is not None:
                call_session.caller_video_enabled = bool(video_enabled)
                update_fields.append("caller_video_enabled")
        else:
            if muted is not None:
                call_session.callee_muted = bool(muted)
                update_fields.append("callee_muted")
            if video_enabled is not None:
                call_session.callee_video_enabled = bool(video_enabled)
                update_fields.append("callee_video_enabled")
        if update_fields:
            update_fields.append("updated_at")
            call_session.save(update_fields=update_fields)
        return Response({"success": True, "call_session": _serialize_call_session(call_session, profile)})


class MessageUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(UserProfile, user_id=request.user)
        unread_count = DirectMessage.objects.filter(recipient=profile, read=False).count()
        return Response({"unread_count": unread_count})


class MediaUploadView(APIView):
    """Upload media (image/video) to Cloudinary and return the public URL."""
    permission_classes = [permissions.IsAuthenticated]

    # Max sizes
    MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
    MAX_FILE_SIZE = 25 * 1024 * 1024    # 25 MB

    ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'}
    ALLOWED_FILE_TYPES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain',
        'text/csv',
        'application/zip',
        'application/x-zip-compressed',
    }

    def post(self, request):
        from django.conf import settings
        import cloudinary.uploader

        media = request.FILES.get('file') or request.FILES.get('media')
        if not media:
            return Response({'error': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)

        content_type = getattr(media, 'content_type', '') or ''
        is_image = content_type in self.ALLOWED_IMAGE_TYPES
        is_video = content_type in self.ALLOWED_VIDEO_TYPES
        is_file = content_type in self.ALLOWED_FILE_TYPES

        if not is_image and not is_video and not is_file:
            return Response(
                {'error': 'Unsupported file type. Allowed: JPEG, PNG, GIF, WEBP, MP4, MOV, AVI, WEBM, PDF, DOCX, XLSX, PPTX, TXT, CSV, ZIP'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_size = self.MAX_IMAGE_SIZE if is_image else self.MAX_VIDEO_SIZE if is_video else self.MAX_FILE_SIZE
        if media.size > max_size:
            limit_mb = max_size // (1024 * 1024)
            return Response(
                {'error': f'File too large. Maximum size is {limit_mb}MB'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not settings.CLOUDINARY_ENABLED:
            # Dev fallback: return a placeholder so the UI doesn't crash
            return Response(
                {'url': '', 'name': media.name, 'error': 'Cloudinary not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            resource_type = 'image' if is_image else 'video' if is_video else 'raw'

            # Map upload context → Cloudinary folder so every asset type
            # lands in its own organised directory under herald/.
            context = (request.data.get('context') or request.query_params.get('context') or 'post').strip()

            FOLDER_MAP = {
                # Feed posts
                'post':               f'heraldsocial/posts/{resource_type}s',
                # Community posts
                'community_post':     f'heraldsocial/communities/posts/{resource_type}s',
                # Community banner / cover image
                'community_banner':   'heraldsocial/communities/banners',
                # News article images
                'news':               'heraldsocial/news/images',
                # Cause cover images
                'cause':              'heraldsocial/causes/images',
                # User profile cover photos
                'profile_cover':      'heraldsocial/profiles/covers',
                # Direct message attachments
                'dm_attachment':      f'heraldsocial/messages/{"media" if resource_type != "raw" else "files"}',
            }

            folder = FOLDER_MAP.get(context, f'heraldsocial/posts/{resource_type}s')

            result = cloudinary.uploader.upload(
                media,
                folder=folder,
                resource_type=resource_type,
                # Auto-quality & format optimisation for images
                quality='auto' if is_image else None,
                fetch_format='auto' if is_image else None,
            )

            return Response(
                {
                    'url': result['secure_url'],
                    'public_id': result['public_id'],
                    'folder': folder,
                    'name': media.name,
                    'size': media.size,
                    'content_type': content_type,
                    'resource_type': resource_type,
                    'media_type': 'image' if is_image else 'video' if is_video else 'file',
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
