from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_directmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='auth_provider',
            field=models.CharField(default='password', max_length=32),
        ),
        migrations.AddField(
            model_name='user',
            name='kingschat_id',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='kingschat_username',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
