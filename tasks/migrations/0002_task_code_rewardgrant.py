from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS tasks (
                id uuid PRIMARY KEY,
                title varchar(200) NOT NULL,
                description text NULL,
                task_type varchar(20) NOT NULL,
                reward integer NOT NULL,
                target integer NOT NULL,
                created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_tasks (
                id uuid PRIMARY KEY,
                progress integer NOT NULL DEFAULT 0,
                completed boolean NOT NULL DEFAULT FALSE,
                claimed boolean NOT NULL DEFAULT FALSE,
                completed_at timestamp with time zone NULL,
                created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
                task_id uuid NOT NULL REFERENCES tasks(id) DEFERRABLE INITIALLY DEFERRED,
                user_id uuid NOT NULL REFERENCES users_user(id) DEFERRABLE INITIALLY DEFERRED
            );

            CREATE UNIQUE INDEX IF NOT EXISTS user_tasks_user_id_task_id_uniq
                ON user_tasks(user_id, task_id);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddField(
            model_name='task',
            name='code',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.CreateModel(
            name='RewardGrant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action_code', models.CharField(max_length=64)),
                ('source_key', models.CharField(max_length=160)),
                ('points', models.IntegerField()),
                ('description', models.TextField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reward_grants', to='users.user')),
            ],
            options={
                'db_table': 'reward_grants',
                'unique_together': {('user', 'action_code', 'source_key')},
            },
        ),
        migrations.AddIndex(
            model_name='rewardgrant',
            index=models.Index(fields=['user', '-created_at'], name='reward_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='rewardgrant',
            index=models.Index(fields=['action_code', '-created_at'], name='reward_action_created_idx'),
        ),
    ]
