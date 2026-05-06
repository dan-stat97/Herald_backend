from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('livestreams', '0005_livestream_performance_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='livestream',
            name='amplifies_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='livestream',
            name='likes_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='livestream',
            name='views_count',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='StreamAmplify',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amplifies', to='livestreams.livestream')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stream_amplifies', to='users.user')),
            ],
            options={
                'db_table': 'stream_amplifies',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='StreamLike',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='livestreams.livestream')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stream_likes', to='users.user')),
            ],
            options={
                'db_table': 'stream_likes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='streamamplify',
            constraint=models.UniqueConstraint(fields=('stream', 'user'), name='uniq_stream_amplify_stream_user'),
        ),
        migrations.AddConstraint(
            model_name='streamlike',
            constraint=models.UniqueConstraint(fields=('stream', 'user'), name='uniq_stream_like_stream_user'),
        ),
        migrations.AddIndex(
            model_name='streamamplify',
            index=models.Index(fields=['user', '-created_at'], name='stream_amp_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='streamamplify',
            index=models.Index(fields=['stream', '-created_at'], name='stream_amp_stream_created_idx'),
        ),
        migrations.AddIndex(
            model_name='streamlike',
            index=models.Index(fields=['user', '-created_at'], name='stream_like_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='streamlike',
            index=models.Index(fields=['stream', '-created_at'], name='stream_like_stream_created_idx'),
        ),
    ]
