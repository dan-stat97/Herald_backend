"""
Migration 0003 – add missing columns to news_articles on production.

The production news_articles table was created before 0002 (NewsArticle model),
so migrate_safe faked 0002 and the columns never got added.
This migration uses RunSQL-only ops so migrate_safe won't fake it.
"""
from django.db import migrations


class _PgOnlyRunSQL(migrations.RunSQL):
    """Runs SQL only on PostgreSQL; silently skips on SQLite (local dev)."""

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_newsarticle_newsbookmark_newslike'),
    ]

    operations = [
        _PgOnlyRunSQL(
            sql="""
                ALTER TABLE news_articles
                    ADD COLUMN IF NOT EXISTS category     VARCHAR(50)  NOT NULL DEFAULT 'general',
                    ADD COLUMN IF NOT EXISTS source_url   VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS image_url    VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS likes_count  INTEGER      NOT NULL DEFAULT 0;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
