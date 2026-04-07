from django.core.management import call_command
from django.db import migrations


def seed_official_newsroom(apps, schema_editor):
    call_command('seed_data')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_seed_news_and_users'),
    ]

    operations = [
        migrations.RunPython(seed_official_newsroom, migrations.RunPython.noop),
    ]
