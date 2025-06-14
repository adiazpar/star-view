"""
Development settings for Event Horizon project.
"""

from .base import *

# Development-specific overrides
DEBUG = True

# Additional development apps (only if installed)
try:
    import django_extensions
    INSTALLED_APPS += ['django_extensions']  # For shell_plus and other dev tools
except ImportError:
    pass

# Development database (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'TEST': {
            'NAME': ':memory:'
        },
    }
}

# Development email backend (console for testing)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Override with SendGrid for actual email testing if needed
if not os.getenv('USE_CONSOLE_EMAIL', False):
    EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'

# Development security settings
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'nyx.local']
CSRF_TRUSTED_ORIGINS = []

# Development logging - more verbose
LOGGING['loggers']['stars_app']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'INFO'

# Development cache (dummy cache for testing)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Development static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Development debugging
INTERNAL_IPS = ['127.0.0.1']

# Disable API limits for development
DISABLE_EXTERNAL_APIS = os.getenv('DISABLE_EXTERNAL_APIS', 'False') == 'True'