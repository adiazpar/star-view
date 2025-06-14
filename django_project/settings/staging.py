"""
Staging settings for Event Horizon project.
"""

from .base import *

# Staging should be close to production but with some debug features
DEBUG = False

# Staging database - can be PostgreSQL or SQLite depending on needs
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('STAGING_DB_NAME', 'event_horizon_staging'),
        'USER': os.getenv('STAGING_DB_USER', 'postgres'),
        'PASSWORD': os.getenv('STAGING_DB_PASSWORD', ''),
        'HOST': os.getenv('STAGING_DB_HOST', 'localhost'),
        'PORT': os.getenv('STAGING_DB_PORT', '5432'),
    }
}

# Staging email configuration
SENDGRID_SANDBOX_MODE_IN_DEBUG = True  # Don't send real emails in staging

# Staging security settings
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')

# Staging logging - moderate verbosity
LOGGING['loggers']['stars_app']['level'] = 'INFO'
LOGGING['loggers']['django']['level'] = 'WARNING'

# Staging cache - use Redis if available
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# Staging static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Enable WhiteNoise middleware for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Security headers for staging
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True