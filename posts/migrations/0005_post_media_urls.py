from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_post_bookmarks_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='media_urls',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='scheduledpost',
            name='media_urls',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
