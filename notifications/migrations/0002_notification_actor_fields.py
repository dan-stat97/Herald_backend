from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        # Make related_resource fields nullable (they were required before)
        migrations.AlterField(
            model_name='notification',
            name='related_resource_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='related_resource_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        # Expand notification_type choices
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('like', 'Like'), ('comment', 'Comment'), ('follow', 'Follow'),
                    ('share', 'Share'), ('reward', 'Reward'), ('system', 'System'),
                ],
                max_length=20,
            ),
        ),
        # Add actor fields
        migrations.AddField(
            model_name='notification',
            name='actor_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='actor_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='actor_avatar',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='actor_verified',
            field=models.BooleanField(default=False),
        ),
    ]
