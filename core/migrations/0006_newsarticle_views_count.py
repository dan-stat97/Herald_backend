from django.db import migrations, models


class _PgOnlyRunSQL(migrations.RunSQL):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_seed_official_newsroom'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                _PgOnlyRunSQL(
                    sql="""
                        ALTER TABLE news_articles
                            ADD COLUMN IF NOT EXISTS views_count INTEGER NOT NULL DEFAULT 0;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='newsarticle',
                    name='views_count',
                    field=models.IntegerField(default=0),
                ),
            ],
        ),
    ]
