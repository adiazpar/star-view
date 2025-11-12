# ----------------------------------------------------------------------------------------------------- #
# This celery.py file configures Celery for asynchronous task processing:                               #
#                                                                                                       #
# Purpose:                                                                                              #
# Sets up Celery with Redis as the message broker for handling background tasks like external API       #
# calls (Mapbox enrichment), email sending, and other time-consuming operations.                        #
#                                                                                                       #
# Key Features:                                                                                         #
# - Redis as message broker (already used for caching)                                                  #
# - Automatic task discovery from all Django apps                                                       #
# - Timezone-aware scheduling                                                                           #
# - Environment-based configuration                                                                     #
#                                                                                                       #
# Usage:                                                                                                #
# Start Celery worker: celery -A django_project worker --loglevel=info                                  #
# Monitor tasks: celery -A django_project events                                                        #
# ----------------------------------------------------------------------------------------------------- #

import os
import logging
from celery import Celery

# Configure module logger
logger = logging.getLogger(__name__)

# Set Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

# Create Celery app instance
app = Celery('django_project')

# Load configuration from Django settings with 'CELERY_' prefix
# Example: CELERY_BROKER_URL in settings.py becomes broker_url in Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed Django apps
# Looks for tasks.py files in each app directory
app.autodiscover_tasks()


# Optional: Task for debugging Celery setup
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.debug('Celery debug task - Request: %r', self.request)
