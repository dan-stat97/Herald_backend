from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0009_community_invite'),
    ]

    operations = [
        migrations.AddField(
            model_name='communitypost',
            name='views_count',
            field=models.IntegerField(default=0),
        ),
    ]
