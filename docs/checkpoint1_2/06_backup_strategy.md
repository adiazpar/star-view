# Database Backup Strategy

## Overview
Implemented a comprehensive backup system to protect application data through automated backup creation, retention policies, and recovery procedures. This system supports both development and production environments with multiple backup formats.

## Why Database Backups Were Needed

### Data Protection Risks

#### Development Risks
- **Accidental data deletion**: Developer mistakes during testing
- **Migration failures**: Database schema changes gone wrong
- **Corrupted databases**: Hardware failures or system crashes
- **Code bugs**: Logic errors that corrupt data
- **Testing cleanup**: Accidental deletion of important test data

#### Production Risks
- **Hardware failures**: Server crashes, disk failures
- **Human error**: Accidental DROP TABLE or DELETE commands
- **Security breaches**: Malicious data deletion or corruption
- **Software bugs**: Application errors that damage data
- **Natural disasters**: Data center outages or destruction

### Real-World Scenarios

#### Without Backups
```python
# Scenario: Developer accidentally runs wrong migration
python manage.py migrate --fake stars_app zero
# Result: All star location data lost forever
# Recovery: Impossible without backups
```

#### With Backups
```python
# Same scenario, but with backup system
python manage.py migrate --fake stars_app zero
# Recovery: Restore from automated daily backup
python manage.py loaddata backups/backup_20241214_020000.json
# Result: Data restored, minimal downtime
```

### Compliance and Business Requirements
- **Data retention policies**: Many organizations require data backups
- **Disaster recovery**: Business continuity planning
- **Version control**: Ability to restore to specific points in time
- **Testing safety**: Safe environment for testing destructive operations

## What Was Implemented

### 1. Backup Management Command
**File**: `stars_app/management/commands/backup_db.py`

```python
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
```

### 2. SQL Backup Implementation (PostgreSQL)
```python
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
        '--clean',           # Include DROP statements
        '--no-owner',        # Don't include ownership commands
        '--no-privileges',   # Don't include privilege commands
        f'--file={backup_file}'
    ]
    
    # Set password via environment variable for security
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['PASSWORD']
    
    try:
        subprocess.run(cmd, env=env, check=True)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created backup: {backup_file}')
        )
    except subprocess.CalledProcessError as e:
        raise CommandError(f'Backup failed: {e}')
```

### 3. Django Fixtures Backup Implementation
```python
def create_django_backup(self, output_dir, timestamp):
    """Create Django fixtures backup"""
    backup_file = os.path.join(output_dir, f'backup_{timestamp}.json')
    
    # Use Django's dumpdata command
    from django.core.management import call_command
    
    try:
        with open(backup_file, 'w') as f:
            call_command(
                'dumpdata',
                'stars_app',        # Only backup stars_app data
                stdout=f,
                indent=2,           # Pretty-printed JSON
                natural_foreign=True,    # Use natural keys for foreign keys
                natural_primary=True     # Use natural keys for primary keys
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created backup: {backup_file}')
        )
    except Exception as e:
        raise CommandError(f'Backup failed: {e}')
```

### 4. Automated Backup Script
**File**: `scripts/backup_cron.sh`

```bash
#!/bin/bash

# Database backup script for Event Horizon
# Add to crontab for automated backups
# Example: 0 2 * * * /path/to/webapp/scripts/backup_cron.sh

# Set environment variables
cd /Users/adiaz/webapp
source djvenv/bin/activate

# Create backup
python manage.py backup_db --output-dir=backups --format=json

# Keep only last 7 backups (1 week retention)
find backups -name "backup_*.json" -type f -mtime +7 -delete

# Log completion
echo "$(date): Database backup completed" >> logs/backup.log
```

## Usage Examples

### Manual Backup Creation

#### JSON Format (Works with any database)
```bash
# Basic backup
python manage.py backup_db

# Custom directory and format
python manage.py backup_db --output-dir=my_backups --format=json

# Output:
# Successfully created backup: backups/backup_20241214_143022.json
```

#### SQL Format (PostgreSQL only)
```bash
# PostgreSQL dump format
python manage.py backup_db --format=sql

# Output:
# Successfully created backup: backups/backup_20241214_143022.sql
```

### Automated Backup Setup

#### Cron Job Configuration
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /Users/adiaz/webapp/scripts/backup_cron.sh

# Add weekly full backup (Sundays at 3 AM)
0 3 * * 0 /Users/adiaz/webapp/scripts/backup_cron.sh

# Add hourly backup during business hours (weekdays 9 AM - 5 PM)
0 9-17 * * 1-5 /Users/adiaz/webapp/scripts/backup_cron.sh
```

#### Systemd Timer (Linux alternative to cron)
```ini
# /etc/systemd/system/event-horizon-backup.timer
[Unit]
Description=Run Event Horizon backup daily
Requires=event-horizon-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

### Data Restoration

#### From JSON Backup
```bash
# Restore complete backup
python manage.py loaddata backups/backup_20241214_143022.json

# Restore specific models
python manage.py loaddata backups/backup_20241214_143022.json --app stars_app

# Clear database first, then restore
python manage.py flush --noinput
python manage.py loaddata backups/backup_20241214_143022.json
```

#### From SQL Backup (PostgreSQL)
```bash
# Drop and recreate database
dropdb event_horizon_dev
createdb event_horizon_dev

# Restore from SQL backup
psql -U postgres -d event_horizon_dev -f backups/backup_20241214_143022.sql

# Or restore using Django
python manage.py dbshell < backups/backup_20241214_143022.sql
```

## Backup Formats Comparison

### JSON Format (Django Fixtures)

#### Advantages
- ✅ **Database agnostic**: Works with SQLite, PostgreSQL, MySQL
- ✅ **Human readable**: Can inspect and edit backup files
- ✅ **Selective restore**: Can restore specific models or records
- ✅ **Django integrated**: Uses Django's serialization system
- ✅ **Version control friendly**: Text format works well with git

#### Disadvantages
- ❌ **Larger file size**: JSON is more verbose than binary formats
- ❌ **Slower for large datasets**: Text parsing overhead
- ❌ **No schema information**: Only data, not database structure
- ❌ **Django specific**: Can't be used with other tools

#### Use Cases
- Development environments
- Small to medium datasets
- When you need to inspect backup contents
- Cross-database migrations
- Version-controlled backups

### SQL Format (PostgreSQL pg_dump)

#### Advantages
- ✅ **Complete backup**: Includes schema, data, indexes, constraints
- ✅ **Fast restore**: Binary format for large datasets
- ✅ **Industry standard**: Compatible with standard PostgreSQL tools
- ✅ **Compression support**: Can be compressed for storage
- ✅ **Incremental backups**: Supports advanced backup strategies

#### Disadvantages
- ❌ **Database specific**: Only works with PostgreSQL
- ❌ **Binary format**: Can't easily inspect contents
- ❌ **Requires pg_dump**: PostgreSQL tools must be installed
- ❌ **Less flexible**: All-or-nothing restore approach

#### Use Cases
- Production environments
- Large datasets
- Complete disaster recovery
- Database-to-database migrations
- When backup speed is critical

## Backup Strategy Recommendations

### Development Environment
```bash
# Daily JSON backups with 1-week retention
0 2 * * * python manage.py backup_db --format=json
find backups -name "backup_*.json" -mtime +7 -delete
```

**Rationale**:
- JSON format for flexibility
- Daily frequency sufficient for development
- Short retention to save disk space
- Easy to restore specific data

### Staging Environment
```bash
# Daily JSON backups with 2-week retention
0 2 * * * python manage.py backup_db --format=json
find backups -name "backup_*.json" -mtime +14 -delete

# Weekly SQL backups with 1-month retention
0 3 * * 0 python manage.py backup_db --format=sql
find backups -name "backup_*.sql" -mtime +30 -delete
```

**Rationale**:
- Both formats for different recovery scenarios
- Longer retention for testing purposes
- Weekly full backups for major issues

### Production Environment
```bash
# Multiple backup strategies:

# Hourly incremental backups during business hours
0 9-17 * * 1-5 pg_dump --incremental ...

# Daily full backups with 30-day retention
0 2 * * * python manage.py backup_db --format=sql
find backups -name "backup_*.sql" -mtime +30 -delete

# Weekly offsite backups with 6-month retention
0 3 * * 0 python manage.py backup_db --format=sql && rsync backup.sql offsite-server:
```

**Rationale**:
- Multiple backup frequencies for different recovery scenarios
- Long retention for compliance and disaster recovery
- Offsite storage for disaster protection

## Retention Policies

### Automatic Cleanup Implementation
```bash
# In backup_cron.sh script
# Keep daily backups for 7 days
find backups -name "backup_*.json" -type f -mtime +7 -delete

# Keep weekly backups for 30 days  
find backups -name "weekly_backup_*.sql" -type f -mtime +30 -delete

# Keep monthly backups for 1 year
find backups -name "monthly_backup_*.sql" -type f -mtime +365 -delete
```

### Custom Retention Script
```python
# scripts/cleanup_backups.py
import os
import glob
from datetime import datetime, timedelta

def cleanup_backups(backup_dir='backups'):
    now = datetime.now()
    
    # Keep daily backups for 1 week
    daily_cutoff = now - timedelta(days=7)
    
    # Keep weekly backups for 1 month  
    weekly_cutoff = now - timedelta(days=30)
    
    # Keep monthly backups for 1 year
    monthly_cutoff = now - timedelta(days=365)
    
    for backup_file in glob.glob(f'{backup_dir}/backup_*.json'):
        file_time = datetime.fromtimestamp(os.path.getmtime(backup_file))
        
        # Determine backup type and apply appropriate retention
        if 'daily' in backup_file and file_time < daily_cutoff:
            os.remove(backup_file)
        elif 'weekly' in backup_file and file_time < weekly_cutoff:
            os.remove(backup_file)
        elif 'monthly' in backup_file and file_time < monthly_cutoff:
            os.remove(backup_file)
```

## Monitoring and Alerting

### Backup Success Monitoring
```python
# stars_app/management/commands/check_backups.py
class Command(BaseCommand):
    help = 'Check backup health and alert if issues found'
    
    def handle(self, *args, **options):
        backup_dir = 'backups'
        now = datetime.now()
        
        # Check if recent backup exists (within 25 hours)
        cutoff = now - timedelta(hours=25)
        
        recent_backups = []
        for backup_file in glob.glob(f'{backup_dir}/backup_*.json'):
            file_time = datetime.fromtimestamp(os.path.getmtime(backup_file))
            if file_time >= cutoff:
                recent_backups.append(backup_file)
        
        if not recent_backups:
            # Send alert - no recent backups found
            self.send_backup_alert("No recent backups found!")
            self.stdout.write(self.style.ERROR('No recent backups found!'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Found {len(recent_backups)} recent backups')
            )
    
    def send_backup_alert(self, message):
        # Send email, Slack notification, etc.
        pass
```

### Backup Verification
```python
def verify_backup(backup_file):
    """Verify backup integrity by attempting to load it"""
    try:
        if backup_file.endswith('.json'):
            # Verify JSON backup
            with open(backup_file, 'r') as f:
                data = json.load(f)
                return len(data) > 0
        
        elif backup_file.endswith('.sql'):
            # Verify SQL backup (basic syntax check)
            with open(backup_file, 'r') as f:
                content = f.read()
                return 'CREATE TABLE' in content and 'INSERT INTO' in content
        
        return False
    except Exception as e:
        print(f"Backup verification failed: {e}")
        return False
```

## Security Considerations

### Backup File Protection
```bash
# Set secure permissions on backup directory
chmod 700 backups/
chmod 600 backups/*.json
chmod 600 backups/*.sql

# Use encrypted storage for sensitive data
gpg --cipher-algo AES256 --compress-algo 1 --symmetric backup_20241214.json
```

### Password Security
```python
# In backup command - use environment variables, not hardcoded passwords
env = os.environ.copy()
env['PGPASSWORD'] = db_config['PASSWORD']  # From Django settings

# Never store passwords in backup scripts or cron jobs
# Use .pgpass file or environment variables instead
```

### Access Control
```bash
# Restrict backup script execution
chown root:backup-group backup_cron.sh
chmod 750 backup_cron.sh

# Use dedicated backup user with minimal privileges
sudo -u backup-user python manage.py backup_db
```

## Testing Backup and Recovery

### Backup Testing Script
```python
# tests/test_backup_restore.py
class BackupRestoreTest(TestCase):
    def test_backup_and_restore_cycle(self):
        # Create test data
        location = ViewingLocation.objects.create(
            name="Test Location",
            latitude=40.0,
            longitude=-74.0,
            quality_score=85
        )
        
        # Create backup
        backup_file = 'test_backup.json'
        call_command('backup_db', format='json', output_dir='test_backups')
        
        # Clear database
        ViewingLocation.objects.all().delete()
        self.assertEqual(ViewingLocation.objects.count(), 0)
        
        # Restore from backup
        call_command('loaddata', f'test_backups/{backup_file}')
        
        # Verify data restored
        restored_location = ViewingLocation.objects.get(name="Test Location")
        self.assertEqual(restored_location.latitude, 40.0)
        self.assertEqual(restored_location.quality_score, 85)
        
        # Cleanup
        os.remove(f'test_backups/{backup_file}')
```

### Disaster Recovery Testing
```bash
# Full disaster recovery test procedure

# 1. Create known data state
python manage.py loaddata test_fixtures.json

# 2. Create backup
python manage.py backup_db --format=sql

# 3. Simulate disaster (drop database)
dropdb event_horizon_test
createdb event_horizon_test

# 4. Restore from backup
psql -d event_horizon_test -f backups/backup_latest.sql

# 5. Verify data integrity
python manage.py test tests.test_data_integrity
```

## Future Enhancements

### Cloud Storage Integration
```python
# Upload backups to AWS S3, Google Cloud, etc.
def upload_to_cloud(backup_file):
    import boto3
    
    s3 = boto3.client('s3')
    s3.upload_file(
        backup_file, 
        'event-horizon-backups', 
        f'database/{os.path.basename(backup_file)}'
    )
```

### Incremental Backups
```python
# Only backup changed data since last backup
def create_incremental_backup():
    last_backup_time = get_last_backup_timestamp()
    
    # Only backup records modified since last backup
    call_command(
        'dumpdata', 
        'stars_app',
        where=f"updated_at > '{last_backup_time}'"
    )
```

### Real-time Replication
```sql
-- PostgreSQL streaming replication for real-time backup
-- Configure in postgresql.conf:
wal_level = replica
max_wal_senders = 3
checkpoint_segments = 8
wal_keep_segments = 8
```

This comprehensive backup strategy ensures data protection across all environments while providing flexible recovery options for different scenarios.