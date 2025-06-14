#!/bin/bash

# Database backup script for Event Horizon
# Add to crontab for automated backups
# Example: 0 2 * * * /path/to/webapp/scripts/backup_cron.sh

# Set environment variables
cd /Users/adiaz/webapp
source djvenv/bin/activate

# Create backup
python manage.py backup_db --output-dir=backups --format=json

# Keep only last 7 backups
find backups -name "backup_*.json" -type f -mtime +7 -delete

# Log completion
echo "$(date): Database backup completed" >> logs/backup.log