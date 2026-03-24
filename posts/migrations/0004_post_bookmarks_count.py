from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_post_interactions'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='bookmarks_count',
            field=models.IntegerField(default=0),
        ),
    ]
