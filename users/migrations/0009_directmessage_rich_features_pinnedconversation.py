import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_user_phone_number_directmessage_read_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='directmessage',
            name='attachments',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='deleted_for_everyone_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='deleted_for_recipient',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='deleted_for_sender',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='edited_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='forwarded_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='forwards', to='users.directmessage'),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='kind',
            field=models.CharField(choices=[('text', 'Text'), ('image', 'Image'), ('video', 'Video'), ('gif', 'GIF'), ('file', 'File'), ('audio_call', 'Audio Call'), ('video_call', 'Video Call')], default='text', max_length=20),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='metadata',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='reactions',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='reply_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='thread_replies', to='users.directmessage'),
        ),
        migrations.AlterField(
            model_name='directmessage',
            name='content',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.CreateModel(
            name='PinnedConversation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pinned_conversations', to='users.user')),
                ('peer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pinned_by_users', to='users.user')),
            ],
            options={
                'db_table': 'pinned_conversations',
                'ordering': ['created_at'],
                'unique_together': {('owner', 'peer')},
            },
        ),
    ]
