from django.contrib.auth import get_user_model
from django.test import TestCase

from users.models import User

from .models import AdminRoleAssignment
from .permissions import build_admin_context, sync_staff_flag


class AdminRolePermissionsTests(TestCase):
    def setUp(self):
        auth_user_model = get_user_model()
        self.auth_user = auth_user_model.objects.create_user(
            username='opslead',
            email='opslead@example.com',
            password='password123',
        )
        self.profile = User.objects.create(
            user_id=self.auth_user,
            username='opslead',
            display_name='Ops Lead',
            email='opslead@example.com',
        )

    def test_assignment_drives_context_permissions(self):
        AdminRoleAssignment.objects.create(user=self.profile, role=AdminRoleAssignment.ROLE_MODERATOR)
        sync_staff_flag(self.profile)
        self.auth_user.refresh_from_db()

        context = build_admin_context(self.auth_user)

        self.assertTrue(context['is_admin'])
        self.assertEqual(context['role'], AdminRoleAssignment.ROLE_MODERATOR)
        self.assertIn('reports.manage', context['permissions'])
        self.assertTrue(self.auth_user.is_staff)

    def test_staff_user_without_assignment_falls_back_to_admin(self):
        self.auth_user.is_staff = True
        self.auth_user.save(update_fields=['is_staff'])

        context = build_admin_context(self.auth_user)

        self.assertTrue(context['is_admin'])
        self.assertEqual(context['role'], AdminRoleAssignment.ROLE_ADMIN)
        self.assertEqual(context['source'], 'django_staff')
