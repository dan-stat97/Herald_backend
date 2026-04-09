import uuid

from core.models import Profiles


def ensure_legacy_profile(user_profile):
    if not user_profile or not getattr(user_profile, 'user_id_id', None):
        return None

    defaults = {
        'id': uuid.uuid4(),
        'username': (user_profile.username or f'user{user_profile.user_id_id}')[:50],
        'full_name': (user_profile.full_name or user_profile.display_name or user_profile.username or '')[:100] or None,
        'display_name': user_profile.display_name or user_profile.username,
        'verified': bool(getattr(user_profile, 'is_verified', False)),
        'pro_status': bool(getattr(user_profile, 'is_creator', False)),
        'avatar_url': user_profile.avatar_url,
    }

    legacy_profile, created = Profiles.objects.get_or_create(
        user_id=user_profile.user_id_id,
        defaults=defaults,
    )

    updated_fields = []
    desired_username = (user_profile.username or legacy_profile.username or f'user{user_profile.user_id_id}')[:50]
    desired_full_name = (user_profile.full_name or user_profile.display_name or user_profile.username or '')[:100] or None
    desired_display_name = user_profile.display_name or user_profile.username
    desired_verified = bool(getattr(user_profile, 'is_verified', False))
    desired_pro_status = bool(getattr(user_profile, 'is_creator', False))
    desired_avatar_url = user_profile.avatar_url

    if legacy_profile.username != desired_username:
        legacy_profile.username = desired_username
        updated_fields.append('username')
    if legacy_profile.full_name != desired_full_name:
        legacy_profile.full_name = desired_full_name
        updated_fields.append('full_name')
    if legacy_profile.display_name != desired_display_name:
        legacy_profile.display_name = desired_display_name
        updated_fields.append('display_name')
    if legacy_profile.verified != desired_verified:
        legacy_profile.verified = desired_verified
        updated_fields.append('verified')
    if legacy_profile.pro_status != desired_pro_status:
        legacy_profile.pro_status = desired_pro_status
        updated_fields.append('pro_status')
    if legacy_profile.avatar_url != desired_avatar_url:
        legacy_profile.avatar_url = desired_avatar_url
        updated_fields.append('avatar_url')

    if updated_fields and not created:
        legacy_profile.save(update_fields=updated_fields)

    return legacy_profile


def get_legacy_profile_for_user_profile(user_profile):
    if not user_profile:
        return None
    return Profiles.objects.filter(user_id=user_profile.user_id_id).first() or ensure_legacy_profile(user_profile)
