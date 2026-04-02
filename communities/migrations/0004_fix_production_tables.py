"""
Fix production PostgreSQL schema for communities:

1. community_members had an integer community_id (old pre-UUID schema).
   Drop and recreate with correct UUID FK.

2. communities_communitypost and communities_communitypostlike were never
   created on production because migrate_safe faked migration 0003 after
   detecting the role column already existed on the old community_members.
   Create them now using IF NOT EXISTS so the migration is idempotent.

Using RunSQL only (no CreateModel) so migrate_safe does not fake this migration.
This migration is a no-op on SQLite (local dev); it only runs on PostgreSQL.
"""

from django.db import migrations


FIX_COMMUNITY_MEMBERS = """
DROP TABLE IF EXISTS community_members CASCADE;

CREATE TABLE community_members (
    id             uuid         NOT NULL PRIMARY KEY,
    community_id   uuid         NOT NULL
                   REFERENCES communities_community (id) ON DELETE CASCADE
                   DEFERRABLE INITIALLY DEFERRED,
    user_id        uuid         NOT NULL
                   REFERENCES users_user (id) ON DELETE CASCADE
                   DEFERRABLE INITIALLY DEFERRED,
    role           varchar(20)  NOT NULL DEFAULT 'member',
    joined_at      timestamptz  NOT NULL DEFAULT now(),
    UNIQUE (community_id, user_id)
);
"""

CREATE_COMMUNITY_POST = """
CREATE TABLE IF NOT EXISTS communities_communitypost (
    id              uuid         NOT NULL PRIMARY KEY,
    community_id    uuid         NOT NULL
                    REFERENCES communities_community (id) ON DELETE CASCADE
                    DEFERRABLE INITIALLY DEFERRED,
    author_id       uuid         NOT NULL
                    REFERENCES users_user (id) ON DELETE CASCADE
                    DEFERRABLE INITIALLY DEFERRED,
    content         text         NOT NULL,
    media_url       varchar(200),
    media_type      varchar(20),
    likes_count     integer      NOT NULL DEFAULT 0,
    comments_count  integer      NOT NULL DEFAULT 0,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    updated_at      timestamptz  NOT NULL DEFAULT now()
);
"""

CREATE_COMMUNITY_POST_LIKE = """
CREATE TABLE IF NOT EXISTS communities_communitypostlike (
    id          uuid        NOT NULL PRIMARY KEY,
    post_id     uuid        NOT NULL
                REFERENCES communities_communitypost (id) ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED,
    user_id     uuid        NOT NULL
                REFERENCES users_user (id) ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (post_id, user_id)
);
"""


class _PgOnlyRunSQL(migrations.RunSQL):
    """RunSQL that is silently skipped on non-PostgreSQL databases (e.g. SQLite dev)."""

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0003_add_community_post_and_like'),
        ('users', '0003_directmessage'),
    ]

    operations = [
        _PgOnlyRunSQL(
            sql=FIX_COMMUNITY_MEMBERS,
            reverse_sql='DROP TABLE IF EXISTS community_members CASCADE;',
        ),
        _PgOnlyRunSQL(
            sql=CREATE_COMMUNITY_POST,
            reverse_sql='DROP TABLE IF EXISTS communities_communitypost CASCADE;',
        ),
        _PgOnlyRunSQL(
            sql=CREATE_COMMUNITY_POST_LIKE,
            reverse_sql='DROP TABLE IF EXISTS communities_communitypostlike CASCADE;',
        ),
    ]
