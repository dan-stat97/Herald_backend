"""
One-time cleanup: delete the Grace and duplicate Wonderful kids communities
created during testing before the community 500 bug was fixed.
"""

import uuid
from django.db import migrations


COMMUNITIES_TO_DELETE = [
    # 'Grace' – 0 members, created during buggy period
    uuid.UUID('8ca7fb4a-eacb-47dd-8b0e-363b2ff8b721'),
    # 'Wonderful kids' × 2 – duplicate, both created before join was working
    uuid.UUID('46b977c6-360b-4aa4-8c8a-a3b2530817a0'),
    uuid.UUID('71fd0c0d-cdd3-4153-bb40-3119826f0bbb'),
]


def delete_test_communities(apps, schema_editor):
    Community = apps.get_model('communities', 'Community')
    deleted, _ = Community.objects.filter(id__in=COMMUNITIES_TO_DELETE).delete()
    print(f'  Deleted {deleted} test community row(s).')


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0004_fix_production_tables'),
    ]

    operations = [
        migrations.RunPython(
            delete_test_communities,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
