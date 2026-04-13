from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0007_community_rules'),
        ('users', '0001_initial'),
    ]

    operations = [
        # ── Community new fields ──────────────────────────────────────────────
        migrations.AddField(
            model_name='community',
            name='membership_type',
            field=models.CharField(
                max_length=10,
                choices=[('open', 'Open'), ('request', 'Request to Join'), ('invite', 'Invite Only')],
                default='open',
            ),
        ),
        migrations.AddField(
            model_name='community',
            name='entry_question',
            field=models.TextField(null=True, blank=True),
        ),

        # ── CommunityPost: add is_pinned ──────────────────────────────────────
        migrations.AddField(
            model_name='communitypost',
            name='is_pinned',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterModelOptions(
            name='communitypost',
            options={'ordering': ['-is_pinned', '-created_at']},
        ),

        # ── CommunityJoinRequest ──────────────────────────────────────────────
        migrations.CreateModel(
            name='CommunityJoinRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                    default='pending', max_length=10,
                )),
                ('answer', models.TextField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('community', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='join_requests',
                    to='communities.community',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='community_join_requests',
                    to='users.user',
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to='users.user',
                )),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('community', 'user')},
            },
        ),

        # ── CommunityPostComment ──────────────────────────────────────────────
        migrations.CreateModel(
            name='CommunityPostComment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments',
                    to='communities.communitypost',
                )),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='community_post_comments',
                    to='users.user',
                )),
            ],
            options={'ordering': ['created_at']},
        ),
    ]
