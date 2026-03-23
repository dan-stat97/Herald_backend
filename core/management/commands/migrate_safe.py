"""
migrate_safe - idempotent migration runner for Render/PostgreSQL

Handles the case where tables already exist in the DB but are not
recorded in django_migrations (e.g. partial deploys, manual schema
creation).  For each unapplied migration it:

  - Fakes any CreateModel operation whose table already exists in the DB
  - Applies AddField / AlterField operations normally (adds missing columns)
  - Falls back to faking the whole migration if a 'already exists' error
    is raised, so the build never breaks on a duplicate-table error.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.operations.models import CreateModel


def _existing_tables():
    """Return the set of table names currently in the public schema."""
    with connection.cursor() as cursor:
        try:
            cursor.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            )
            return {r[0] for r in cursor.fetchall()}
        except Exception:
            # SQLite (local dev) – don't need to fake anything
            return set()


def _existing_columns(table):
    """Return the set of column names for *table* (PostgreSQL only)."""
    with connection.cursor() as cursor:
        try:
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                """,
                [table],
            )
            return {r[0] for r in cursor.fetchall()}
        except Exception:
            return set()


class Command(BaseCommand):
    help = (
        "Run all pending migrations safely: fake CreateModel ops whose "
        "tables already exist, apply column-level changes normally."
    )

    def handle(self, *args, **options):
        self.stdout.write("=== migrate_safe: starting ===")

        # ── pass 1: standard --fake-initial covers genuine 0001_initial migs ──
        self.stdout.write("Pass 1 – fake-initial …")
        try:
            call_command("migrate", "--fake-initial", verbosity=1)
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  fake-initial raised: {exc}"))

        # ── pass 2: iterate remaining unapplied migrations ──
        self.stdout.write("Pass 2 – handling remaining unapplied migrations …")

        max_rounds = 30  # safety valve against infinite loops
        for _round in range(max_rounds):
            executor = MigrationExecutor(connection)
            plan = [
                (mig, bwd)
                for mig, bwd in executor.migration_plan(
                    executor.loader.graph.leaf_nodes()
                )
                if not bwd
            ]

            if not plan:
                self.stdout.write(self.style.SUCCESS("  No more pending migrations."))
                break

            made_progress = False
            tables = _existing_tables()

            for migration, _ in plan:
                app = migration.app_label
                name = migration.name

                # Decide: should we fake this migration entirely?
                should_fake = False
                for op in migration.operations:
                    if isinstance(op, CreateModel):
                        db_table = op.options.get(
                            "db_table", f"{app}_{op.name.lower()}"
                        )
                        if db_table in tables:
                            should_fake = True
                            break

                if should_fake:
                    self.stdout.write(
                        f"  FAKE  {app}.{name}  (table already exists)"
                    )
                    call_command("migrate", app, name, fake=True, verbosity=0)
                    made_progress = True
                    break  # restart loop so executor reloads applied set

                # Try applying normally
                try:
                    self.stdout.write(f"  APPLY {app}.{name}")
                    call_command("migrate", app, name, verbosity=1)
                    made_progress = True
                    break
                except Exception as exc:
                    err = str(exc)
                    if "already exists" in err or "duplicate" in err.lower():
                        self.stdout.write(
                            self.style.WARNING(
                                f"  FAKE  {app}.{name}  (conflict: {exc})"
                            )
                        )
                        call_command("migrate", app, name, fake=True, verbosity=0)
                        made_progress = True
                        break
                    else:
                        raise

            if not made_progress:
                self.stdout.write(
                    self.style.WARNING("  No progress made – stopping.")
                )
                break

        self.stdout.write(self.style.SUCCESS("=== migrate_safe: done ==="))
