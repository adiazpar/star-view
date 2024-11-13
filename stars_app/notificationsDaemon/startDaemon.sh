#!/bin/bash

SCRIPT_DIR=$(dirname "$(realpath "$0")")
VENV_PATH="/path/to/venv"  # Update this to your actual venv path
SCRIPT_PATH="$SCRIPT_DIR/notificationsDaemon.py"
LOG_PATH="/var/log/notificationsDaemon.log"

touch "$LOG_PATH"
chmod 664 "$LOG_PATH"

CRON_JOB="40 23 * * * $VENV_PATH/bin/python3 $SCRIPT_PATH >> $LOG_PATH 2>&1"

(crontab -l | grep -F "$SCRIPT_PATH") &>/dev/null

if [ $? -eq 0 ]; then
    echo "Cron job already exists. No changes made."
else
    (crontab -l; echo "$CRON_JOB") | crontab -
    echo "Cron job scheduled to run daily at 11:40 PM."
fi
