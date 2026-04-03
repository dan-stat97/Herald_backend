"""
One-time cleanup: delete all users whose username or email contains 'test'
(case-insensitive). Cascades to user profiles, posts, community memberships, etc.
"""

from django.db import migrations


def delete_test_users(apps, schema_editor):
    # AuthUser is the Django auth user model
    AuthUser = apps.get_model('auth', 'User')
    qs = AuthUser.objects.filter(username__icontains='test') | \
         AuthUser.objects.filter(email__icontains='test')
    count = qs.count()
    qs.delete()
    print(f'  Deleted {count} test auth user(s).')

    # Also clean up orphaned user profiles
    UserProfile = apps.get_model('users', 'User')
    pqs = UserProfile.objects.filter(username__icontains='test')
    pcount = pqs.count()
    pqs.delete()
    print(f'  Deleted {pcount} test profile(s).')


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0005_delete_test_communities'),
    ]

    operations = [
        migrations.RunPython(
            delete_test_users,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
