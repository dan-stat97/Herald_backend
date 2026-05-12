from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_directmessage_rich_features_pinnedconversation'),
    ]

    operations = [
        migrations.CreateModel(
            name='DevicePushToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.CharField(max_length=255, unique=True)),
                ('platform', models.CharField(choices=[('ios', 'iOS'), ('android', 'Android'), ('web', 'Web'), ('unknown', 'Unknown')], default='unknown', max_length=20)),
                ('enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_tokens', to='users.user')),
            ],
            options={
                'db_table': 'device_push_tokens',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='CallSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('mode', models.CharField(choices=[('audio', 'Audio'), ('video', 'Video')], default='audio', max_length=20)),
                ('status', models.CharField(choices=[('ringing', 'Ringing'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('ended', 'Ended'), ('missed', 'Missed'), ('canceled', 'Canceled')], default='ringing', max_length=20)),
                ('room_name', models.CharField(max_length=120)),
                ('room_url', models.URLField()),
                ('caller_muted', models.BooleanField(default=False)),
                ('caller_video_enabled', models.BooleanField(default=True)),
                ('callee_muted', models.BooleanField(default=False)),
                ('callee_video_enabled', models.BooleanField(default=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('callee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_calls', to='users.user')),
                ('caller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_calls', to='users.user')),
                ('related_message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='call_sessions', to='users.directmessage')),
            ],
            options={
                'db_table': 'call_sessions',
                'ordering': ['-created_at'],
            },
        ),
    ]
