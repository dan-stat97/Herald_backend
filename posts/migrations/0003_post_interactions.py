import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_scheduledpost'),
        ('users', '0003_directmessage'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='posts.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_likes', to='users.user')),
            ],
            options={
                'unique_together': {('post', 'user')},
            },
        ),
        migrations.CreateModel(
            name='PostRepost',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reposts', to='posts.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_reposts', to='users.user')),
            ],
            options={
                'unique_together': {('post', 'user')},
            },
        ),
        migrations.CreateModel(
            name='PostBookmark',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookmarks', to='posts.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_bookmarks', to='users.user')),
            ],
            options={
                'unique_together': {('post', 'user')},
            },
        ),
    ]
