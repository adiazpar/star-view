"""
Django Management Command - Database Diagnostics

Outputs database configuration and migration status to help troubleshoot
production deployment issues without shell access.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
import os


class Command(BaseCommand):
    help = 'Diagnose database configuration and migrations'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("DATABASE DIAGNOSTICS")
        self.stdout.write("=" * 80)

        # Environment variables
        self.stdout.write("\n[ENVIRONMENT VARIABLES]")
        self.stdout.write(f"DB_ENGINE: {os.getenv('DB_ENGINE', 'NOT SET (defaults to sqlite3)')}")
        self.stdout.write(f"DB_NAME: {os.getenv('DB_NAME', 'NOT SET')}")
        self.stdout.write(f"DB_USER: {os.getenv('DB_USER', 'NOT SET')}")
        self.stdout.write(f"DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}")
        self.stdout.write(f"DB_PORT: {os.getenv('DB_PORT', 'NOT SET')}")
        self.stdout.write(f"DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}")

        # Django settings
        self.stdout.write("\n[DJANGO DATABASE SETTINGS]")
        db_config = settings.DATABASES['default']
        self.stdout.write(f"Engine: {db_config['ENGINE']}")
        self.stdout.write(f"Name: {db_config.get('NAME', 'N/A')}")
        self.stdout.write(f"User: {db_config.get('USER', 'N/A')}")
        self.stdout.write(f"Host: {db_config.get('HOST', 'N/A')}")
        self.stdout.write(f"Port: {db_config.get('PORT', 'N/A')}")

        # Database connection test
        self.stdout.write("\n[DATABASE CONNECTION]")
        try:
            with connection.cursor() as cursor:
                # Get database type
                db_type = connection.vendor
                self.stdout.write(f"✓ Connected to: {db_type}")

                # Get table list
                if db_type == 'postgresql':
                    cursor.execute("""
                        SELECT tablename
                        FROM pg_catalog.pg_tables
                        WHERE schemaname = 'public'
                        AND tablename LIKE 'starview_%'
                        ORDER BY tablename;
                    """)
                else:  # SQLite
                    cursor.execute("""
                        SELECT name
                        FROM sqlite_master
                        WHERE type='table'
                        AND name LIKE 'starview_%'
                        ORDER BY name;
                    """)

                tables = cursor.fetchall()
                self.stdout.write(f"\n✓ Found {len(tables)} starview tables:")
                for table in tables:
                    self.stdout.write(f"  - {table[0]}")

                # Check for email tables specifically
                email_tables = [t[0] for t in tables if 'email' in t[0]]
                if email_tables:
                    self.stdout.write(f"\n✓ Email monitoring tables found:")
                    for table in email_tables:
                        self.stdout.write(f"  - {table}")
                else:
                    self.stdout.write("\n✗ Email monitoring tables NOT FOUND")
                    self.stdout.write("  Expected: starview_email_bounce, starview_email_complaint, starview_email_suppression")

        except Exception as e:
            self.stdout.write(f"✗ Database connection error: {e}")

        # Migration status
        self.stdout.write("\n[MIGRATION STATUS]")
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

            if plan:
                self.stdout.write(f"✗ {len(plan)} unapplied migrations:")
                for migration, backwards in plan:
                    self.stdout.write(f"  - {migration}")
            else:
                self.stdout.write("✓ All migrations applied")

            # Show applied migrations for starview_app
            applied = executor.loader.applied_migrations
            starview_migrations = [m for m in applied if m[0] == 'starview_app']
            self.stdout.write(f"\n✓ Applied starview_app migrations ({len(starview_migrations)}):")
            for app, name in sorted(starview_migrations):
                self.stdout.write(f"  - {name}")

        except Exception as e:
            self.stdout.write(f"✗ Migration check error: {e}")

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("DIAGNOSTICS COMPLETE")
        self.stdout.write("=" * 80)
