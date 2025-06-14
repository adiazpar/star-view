import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Create a database backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Directory to store backup files'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['sql', 'json'],
            default='json',
            help='Backup format (sql for PostgreSQL, json for Django fixtures)'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        backup_format = options['format']
        
        # Create backup directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if backup_format == 'sql':
            self.create_sql_backup(output_dir, timestamp)
        else:
            self.create_django_backup(output_dir, timestamp)

    def create_sql_backup(self, output_dir, timestamp):
        """Create PostgreSQL dump backup"""
        db_config = settings.DATABASES['default']
        
        if db_config['ENGINE'] != 'django.db.backends.postgresql':
            raise CommandError('SQL backup only supported for PostgreSQL')
        
        backup_file = os.path.join(output_dir, f'backup_{timestamp}.sql')
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            f"--host={db_config.get('HOST', 'localhost')}",
            f"--port={db_config.get('PORT', '5432')}",
            f"--username={db_config['USER']}",
            f"--dbname={db_config['NAME']}",
            '--no-password',
            '--verbose',
            '--clean',
            '--no-owner',
            '--no-privileges',
            f'--file={backup_file}'
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        try:
            subprocess.run(cmd, env=env, check=True)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created backup: {backup_file}')
            )
        except subprocess.CalledProcessError as e:
            raise CommandError(f'Backup failed: {e}')

    def create_django_backup(self, output_dir, timestamp):
        """Create Django fixtures backup"""
        backup_file = os.path.join(output_dir, f'backup_{timestamp}.json')
        
        # Use Django's dumpdata command
        from django.core.management import call_command
        
        try:
            with open(backup_file, 'w') as f:
                call_command(
                    'dumpdata',
                    'stars_app',
                    stdout=f,
                    indent=2,
                    natural_foreign=True,
                    natural_primary=True
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created backup: {backup_file}')
            )
        except Exception as e:
            raise CommandError(f'Backup failed: {e}')