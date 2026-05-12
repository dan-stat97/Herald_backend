from django.db import migrations


TARGET_EMAIL = "somtochukwujoel403@gmail.com"


def bootstrap_super_admin(apps, schema_editor):
    UserProfile = apps.get_model('users', 'User')
    AdminRoleAssignment = apps.get_model('adminpanel', 'AdminRoleAssignment')
    AuthUser = apps.get_model('auth', 'User')

    profile = (
        UserProfile.objects.filter(email__iexact=TARGET_EMAIL).first()
        or UserProfile.objects.filter(user_id__email__iexact=TARGET_EMAIL).first()
    )
    if profile is None:
        return

    AdminRoleAssignment.objects.update_or_create(
        user=profile,
        defaults={'role': 'super_admin', 'created_by': None},
    )

    auth_user = AuthUser.objects.filter(pk=profile.user_id_id).first()
    if auth_user and not auth_user.is_staff:
        auth_user.is_staff = True
        auth_user.save(update_fields=['is_staff'])


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0005_adminroleassignment'),
    ]

    operations = [
        migrations.RunPython(bootstrap_super_admin, migrations.RunPython.noop),
    ]
