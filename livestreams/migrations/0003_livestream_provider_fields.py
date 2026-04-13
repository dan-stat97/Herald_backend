from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('livestreams', '0002_streamchatmessage_streamdonation_streamviewerevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='livestream',
            name='host_token_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='livestream',
            name='ingest_endpoint',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='livestream',
            name='ivs_channel_arn',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='livestream',
            name='ivs_stage_arn',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='livestream',
            name='ivs_stage_rtmps_endpoint',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='livestream',
            name='ivs_stage_whip_endpoint',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='livestream',
            name='playback_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='livestream',
            name='provider',
            field=models.CharField(choices=[('manual', 'Manual'), ('ivs', 'Amazon IVS')], default='manual', max_length=20),
        ),
        migrations.AddField(
            model_name='livestream',
            name='provider_stream_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
