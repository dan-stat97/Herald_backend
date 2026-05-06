from django.db import migrations, models


def normalize_privacy_choices(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(privacy_level='friends_only').update(privacy_level='followers')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_location_user_website'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='allow_message_requests',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='discover_by_email',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='discover_by_phone',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='display_sensitive_media',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='mark_media_sensitive',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='personalization_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='push_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='show_read_receipts',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='privacy_level',
            field=models.CharField(
                choices=[('public', 'Public'), ('followers', 'Followers Only'), ('private', 'Private')],
                default='public',
                max_length=20,
            ),
        ),
        migrations.RunPython(normalize_privacy_choices, migrations.RunPython.noop),
    ]
