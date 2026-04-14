"""
Lightweight notification helpers for community events.

All helpers are fire-and-forget: they silently swallow any exception so a
notification failure never breaks the main request flow.
"""

import logging

logger = logging.getLogger(__name__)


def _create(user, notification_type, title, message,
            actor=None, resource_type=None, resource_id=None):
    try:
        from notifications.models import Notification
        Notification.objects.create(
            user_id=user,
            notification_type=notification_type,
            title=title,
            message=message,
            actor_id=str(actor.id) if actor else None,
            actor_name=actor.display_name or actor.username if actor else None,
            actor_avatar=actor.avatar_url if actor else None,
            actor_verified=actor.is_verified if actor else False,
            related_resource_type=resource_type,
            related_resource_id=str(resource_id) if resource_id else None,
        )
    except Exception as exc:
        logger.warning('community notify failed: %s', exc)


# ── Community join request ────────────────────────────────────────────────────

def notify_join_request_received(community, requester):
    """Notify every admin that a new join request arrived."""
    try:
        from .models import CommunityMember
        admins = (CommunityMember.objects
                  .filter(community=community, role__in=('admin', 'moderator'))
                  .select_related('user'))
        for m in admins:
            if m.user_id == requester.id:
                continue
            _create(
                user=m.user,
                notification_type='system',
                title='New join request',
                message=f'{requester.display_name or requester.username} wants to join {community.name}',
                actor=requester,
                resource_type='community_join_request',
                resource_id=community.id,
            )
    except Exception as exc:
        logger.warning('notify_join_request_received failed: %s', exc)


def notify_join_request_reviewed(join_request):
    """Notify the requester that their request was approved or rejected."""
    try:
        approved = join_request.status == 'approved'
        community = join_request.community
        _create(
            user=join_request.user,
            notification_type='system',
            title=f'Join request {"approved" if approved else "declined"}',
            message=(
                f'You have been approved to join {community.name}!'
                if approved
                else f'Your request to join {community.name} was declined.'
            ),
            actor=join_request.reviewed_by,
            resource_type='community',
            resource_id=community.id,
        )
    except Exception as exc:
        logger.warning('notify_join_request_reviewed failed: %s', exc)


# ── Community post interaction ────────────────────────────────────────────────

def notify_post_liked(post, liker):
    """Notify the post author that someone liked their post (skip self-like)."""
    try:
        if post.author_id == liker.id:
            return
        community = post.community
        _create(
            user=post.author,
            notification_type='like',
            title='Someone liked your post',
            message=f'{liker.display_name or liker.username} liked your post in {community.name}',
            actor=liker,
            resource_type='community_post',
            resource_id=post.id,
        )
    except Exception as exc:
        logger.warning('notify_post_liked failed: %s', exc)


def notify_post_commented(post, commenter, comment_preview):
    """Notify the post author that someone commented (skip self-comment)."""
    try:
        if post.author_id == commenter.id:
            return
        community = post.community
        _create(
            user=post.author,
            notification_type='comment',
            title='New comment on your post',
            message=f'{commenter.display_name or commenter.username} commented in {community.name}: "{comment_preview}"',
            actor=commenter,
            resource_type='community_post',
            resource_id=post.id,
        )
    except Exception as exc:
        logger.warning('notify_post_commented failed: %s', exc)


# ── Community invites ─────────────────────────────────────────────────────────

def notify_invite_sent(invite):
    """Notify the invited user that they have been invited to join a community."""
    try:
        community = invite.community
        _create(
            user=invite.invited_user,
            notification_type='system',
            title='Community invitation',
            message=(
                f'{invite.invited_by.display_name or invite.invited_by.username} '
                f'invited you to join {community.name}'
            ),
            actor=invite.invited_by,
            resource_type='community_invite',
            resource_id=invite.id,
        )
    except Exception as exc:
        logger.warning('notify_invite_sent failed: %s', exc)


def notify_invite_responded(invite):
    """Notify the admin who sent the invite that it was accepted or declined."""
    try:
        accepted = invite.status == 'accepted'
        community = invite.community
        _create(
            user=invite.invited_by,
            notification_type='system',
            title=f'Invite {"accepted" if accepted else "declined"}',
            message=(
                f'{invite.invited_user.display_name or invite.invited_user.username} '
                f'{"accepted" if accepted else "declined"} your invitation to {community.name}'
            ),
            actor=invite.invited_user,
            resource_type='community',
            resource_id=community.id,
        )
    except Exception as exc:
        logger.warning('notify_invite_responded failed: %s', exc)
