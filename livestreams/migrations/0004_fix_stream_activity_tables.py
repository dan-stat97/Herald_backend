"""
Fix production PostgreSQL schema for livestream activity tables.

`migrate_safe` can fake a migration containing multiple CreateModel ops when
one of the tables already exists, which leaves the remaining tables missing in
production. This repair migration uses PostgreSQL IF NOT EXISTS SQL so the
missing livestream activity tables are created idempotently.
"""

from django.db import migrations


CREATE_STREAM_CHAT_MESSAGES = """
CREATE TABLE IF NOT EXISTS stream_chat_messages (
    id          uuid        NOT NULL PRIMARY KEY,
    stream_id   uuid        NOT NULL
                REFERENCES live_streams (id) ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED,
    user_id     uuid        NOT NULL
                REFERENCES users_user (id) ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED,
    message     text        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
"""

CREATE_STREAM_DONATIONS = """
CREATE TABLE IF NOT EXISTS stream_donations (
    id          uuid            NOT NULL PRIMARY KEY,
    stream_id   uuid            NOT NULL
                REFERENCES live_streams (id) ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED,
    user_id     uuid            NOT NULL
                REFERENCES users_user (id) ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED,
    amount      numeric(12, 2)  NOT NULL,
    currency    varchar(20)     NOT NULL DEFAULT 'espees',
    message     text,
    created_at  timestamptz     NOT NULL DEFAULT now()
);
"""

CREATE_STREAM_VIEWER_EVENTS = """
CREATE TABLE IF NOT EXISTS stream_viewer_events (
    id          uuid        NOT NULL PRIMARY KEY,
    stream_id   uuid        NOT NULL
                REFERENCES live_streams (id) ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED,
    user_id     uuid        NOT NULL
                REFERENCES users_user (id) ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED,
    event_type  varchar(10) NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
"""


class _PgOnlyRunSQL(migrations.RunSQL):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('livestreams', '0003_livestream_provider_fields'),
        ('users', '0003_directmessage'),
    ]

    operations = [
        _PgOnlyRunSQL(
            sql=CREATE_STREAM_CHAT_MESSAGES,
            reverse_sql='DROP TABLE IF EXISTS stream_chat_messages CASCADE;',
        ),
        _PgOnlyRunSQL(
            sql=CREATE_STREAM_DONATIONS,
            reverse_sql='DROP TABLE IF EXISTS stream_donations CASCADE;',
        ),
        _PgOnlyRunSQL(
            sql=CREATE_STREAM_VIEWER_EVENTS,
            reverse_sql='DROP TABLE IF EXISTS stream_viewer_events CASCADE;',
        ),
    ]
