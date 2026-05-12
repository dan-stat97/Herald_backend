from __future__ import annotations

from typing import Iterable

from rest_framework import permissions

from .models import AdminRoleAssignment


ROLE_PERMISSIONS = {
    AdminRoleAssignment.ROLE_SUPER_ADMIN: {
        'analytics.view',
        'users.view',
        'users.verify',
        'users.ban',
        'posts.view',
        'reports.view',
        'reports.manage',
        'ads.view',
        'ads.manage',
        'roles.view',
        'roles.manage',
    },
    AdminRoleAssignment.ROLE_ADMIN: {
        'analytics.view',
        'users.view',
        'users.verify',
        'users.ban',
        'posts.view',
        'reports.view',
        'reports.manage',
        'ads.view',
        'ads.manage',
        'roles.view',
    },
    AdminRoleAssignment.ROLE_MODERATOR: {
        'users.view',
        'users.verify',
        'posts.view',
        'reports.view',
        'reports.manage',
    },
    AdminRoleAssignment.ROLE_SUPPORT: {
        'users.view',
        'reports.view',
    },
    AdminRoleAssignment.ROLE_ANALYTICS_VIEWER: {
        'analytics.view',
    },
    AdminRoleAssignment.ROLE_ADS_MANAGER: {
        'analytics.view',
        'ads.view',
        'ads.manage',
    },
}

ALL_ADMIN_PERMISSIONS = set().union(*ROLE_PERMISSIONS.values())


def get_admin_assignment(user):
    if not getattr(user, 'is_authenticated', False):
        return None

    try:
        profile = user.user
    except Exception:
        return None

    try:
        return profile.admin_role_assignment
    except Exception:
        return None


def get_admin_role(user) -> str | None:
    if not getattr(user, 'is_authenticated', False):
        return None

    assignment = get_admin_assignment(user)
    if assignment:
        return assignment.role

    if getattr(user, 'is_superuser', False):
        return AdminRoleAssignment.ROLE_SUPER_ADMIN

    if getattr(user, 'is_staff', False):
        return AdminRoleAssignment.ROLE_ADMIN

    return None


def get_admin_permissions(user) -> set[str]:
    role = get_admin_role(user)
    if not role:
        return set()
    if role == AdminRoleAssignment.ROLE_SUPER_ADMIN:
        return set(ALL_ADMIN_PERMISSIONS)
    return set(ROLE_PERMISSIONS.get(role, set()))


def is_admin_user(user) -> bool:
    return bool(get_admin_role(user))


def sync_staff_flag(profile) -> None:
    auth_user = getattr(profile, 'user_id', None)
    if auth_user is None:
        return

    try:
        assignment = profile.admin_role_assignment
    except Exception:
        assignment = None

    should_be_staff = bool(assignment) or bool(auth_user.is_superuser)
    if auth_user.is_staff != should_be_staff:
        auth_user.is_staff = should_be_staff
        auth_user.save(update_fields=['is_staff'])


def build_admin_context(user) -> dict:
    role = get_admin_role(user)
    permissions_list = sorted(get_admin_permissions(user))
    assignment = get_admin_assignment(user)

    if assignment:
        source = 'assignment'
    elif getattr(user, 'is_superuser', False):
        source = 'django_superuser'
    elif getattr(user, 'is_staff', False):
        source = 'django_staff'
    else:
        source = None

    return {
        'is_admin': bool(role),
        'is_super_admin': role == AdminRoleAssignment.ROLE_SUPER_ADMIN,
        'role': role or 'user',
        'roles': [role] if role else [],
        'permissions': permissions_list,
        'source': source,
    }


class AdminPermission(permissions.BasePermission):
    required_permissions: Iterable[str] = ()

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        role = get_admin_role(request.user)
        if not role:
            return False

        if role == AdminRoleAssignment.ROLE_SUPER_ADMIN:
            return True

        permissions_set = get_admin_permissions(request.user)
        return all(item in permissions_set for item in self.required_permissions)


class CanViewAnalytics(AdminPermission):
    required_permissions = ('analytics.view',)


class CanViewUsers(AdminPermission):
    required_permissions = ('users.view',)


class CanVerifyUsers(AdminPermission):
    required_permissions = ('users.verify',)


class CanBanUsers(AdminPermission):
    required_permissions = ('users.ban',)


class CanViewPosts(AdminPermission):
    required_permissions = ('posts.view',)


class CanViewReports(AdminPermission):
    required_permissions = ('reports.view',)


class CanManageReports(AdminPermission):
    required_permissions = ('reports.manage',)


class CanViewAds(AdminPermission):
    required_permissions = ('ads.view',)


class CanManageAds(AdminPermission):
    required_permissions = ('ads.manage',)


class CanViewRoles(AdminPermission):
    required_permissions = ('roles.view',)


class CanManageRoles(AdminPermission):
    required_permissions = ('roles.manage',)
