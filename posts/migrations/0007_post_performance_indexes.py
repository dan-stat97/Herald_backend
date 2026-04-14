from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_post_views_count'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['-created_at'], name='posts_created_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['author_id', '-created_at'], name='posts_author_created_idx'),
        ),
        migrations.AddIndex(
            model_name='postlike',
            index=models.Index(fields=['user', '-created_at'], name='postlike_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='postrepost',
            index=models.Index(fields=['user', '-created_at'], name='postrepost_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='postbookmark',
            index=models.Index(fields=['user', '-created_at'], name='postbookmark_user_created_idx'),
        ),
    ]
