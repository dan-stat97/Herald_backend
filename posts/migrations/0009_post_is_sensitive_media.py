from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_comment_interactions'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='is_sensitive_media',
            field=models.BooleanField(default=False),
        ),
    ]
