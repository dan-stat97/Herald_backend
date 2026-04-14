from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('livestreams', '0004_fix_stream_activity_tables'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='livestream',
            index=models.Index(fields=['status', '-created_at'], name='streams_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='livestream',
            index=models.Index(fields=['status', 'scheduled_for'], name='streams_status_sched_idx'),
        ),
        migrations.AddIndex(
            model_name='livestream',
            index=models.Index(fields=['user', 'status'], name='streams_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='streamchatmessage',
            index=models.Index(fields=['stream', '-created_at'], name='stream_chat_stream_created_idx'),
        ),
        migrations.AddIndex(
            model_name='streamdonation',
            index=models.Index(fields=['stream', '-created_at'], name='stream_donation_stream_created_idx'),
        ),
        migrations.AddIndex(
            model_name='streamviewerevent',
            index=models.Index(fields=['stream', '-created_at'], name='stream_viewer_stream_created_idx'),
        ),
        migrations.AddIndex(
            model_name='streamviewerevent',
            index=models.Index(fields=['user', '-created_at'], name='stream_viewer_user_created_idx'),
        ),
    ]
