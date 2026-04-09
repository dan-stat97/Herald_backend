from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_user_auth_provider_user_kingschat_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cover_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
