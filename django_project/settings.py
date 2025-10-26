"""
Django settings for Event Horizon project.

Production-ready configuration with:
- PostgreSQL database support
- AWS SES email integration
- Comprehensive security settings
- CORS support for frontend apps
- Rate limiting and throttling
"""

import os
from pathlib import Path
import certifi
from dotenv import load_dotenv

# =============================================================================
# CORE SETTINGS
# =============================================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Site configuration
SITE_ID = 1
SITE_NAME = "Event Horizon"

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# Allowed hosts (comma-separated in .env)
# Development: 127.0.0.1,localhost,nyx.local
# Production: Add your domain (e.g., eventhorizon.com,www.eventhorizon.com)
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,nyx.local').split(',')

# CSRF trusted origins (comma-separated in .env)
# Production: https://eventhorizon.com,https://www.eventhorizon.com
CSRF_TRUSTED_ORIGINS = [origin for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin]

# Security headers (always enabled)
SECURE_BROWSER_XSS_FILTER = True        # Browser XSS filtering
X_FRAME_OPTIONS = 'DENY'                # Prevent clickjacking
SECURE_CONTENT_TYPE_NOSNIFF = True      # Prevent MIME sniffing

# Production-only HTTPS settings (enabled when DEBUG=False)
if not DEBUG:
    SECURE_SSL_REDIRECT = True              # Force HTTPS
    SESSION_COOKIE_SECURE = True            # HTTPS-only session cookies
    CSRF_COOKIE_SECURE = True               # HTTPS-only CSRF cookies
    SECURE_HSTS_SECONDS = 31536000          # 1 year HSTS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True   # HSTS for subdomains
    SECURE_HSTS_PRELOAD = True              # HSTS preload list

# File upload validation settings
MAX_UPLOAD_SIZE_MB = 5
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
ALLOWED_IMAGE_MIMETYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']

# =============================================================================
# INSTALLED APPS
# =============================================================================

INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third-party apps
    'rest_framework',
    'django_crontab',
    'django_filters',
    'corsheaders',              # CORS support (Phase 2)
    'debug_toolbar',            # Development only

    # Project apps
    'stars_app',
]

# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',               # Whitenoise (MUST be after SecurityMiddleware)
    'debug_toolbar.middleware.DebugToolbarMiddleware',          # Debug Toolbar (development)
    'corsheaders.middleware.CorsMiddleware',                    # CORS (before CommonMiddleware)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =============================================================================
# URL CONFIGURATION
# =============================================================================

ROOT_URLCONF = 'django_project.urls'
LOGIN_REDIRECT_URL = '/'

# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =============================================================================
# WSGI
# =============================================================================

WSGI_APPLICATION = 'django_project.wsgi.application'

# =============================================================================
# DATABASE
# =============================================================================

# Database: PostgreSQL (production) or SQLite (development)
# Set DB_ENGINE=postgresql in .env to use PostgreSQL
DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite3')

if DB_ENGINE == 'postgresql':
    # PostgreSQL configuration (production)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'event_horizon'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    # SQLite configuration (development default)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# =============================================================================
# AUTHENTICATION & PASSWORD VALIDATION
# =============================================================================

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Whitenoise configuration for serving static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
TILES_DIR = os.path.join(MEDIA_ROOT, 'tiles')

# Default assets
DEFAULT_PROFILE_PICTURE = '/static/images/default_profile_pic.jpg'

# =============================================================================
# EMAIL CONFIGURATION (AWS SES - Phase 3)
# =============================================================================

# SSL certificate configuration for HTTPS requests (required for Mapbox API)
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['SSL_CERT_FILE'] = certifi.where()

# AWS SES Configuration
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SES_REGION_NAME = os.getenv('AWS_SES_REGION_NAME', 'us-east-1')
AWS_SES_REGION_ENDPOINT = f'email.{AWS_SES_REGION_NAME}.amazonaws.com'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'eventhorizon.alerts@gmail.com')

# AWS SES optimization settings
USE_SES_V2 = True                   # Use newer SESv2 API
AWS_SES_AUTO_THROTTLE = 0.5         # Send at 50% of rate limit (safety factor)

# =============================================================================
# EXTERNAL API CONFIGURATION
# =============================================================================

# Mapbox API (geocoding and elevation)
MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')

# Tile server configuration
TILE_SERVER_URL = os.getenv('TILE_SERVER_URL', 'http://localhost:3001')

# Disable external APIs for testing (set to True in .env when needed)
DISABLE_EXTERNAL_APIS = os.getenv('DISABLE_EXTERNAL_APIS', 'False') == 'True'

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    # Pagination
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,

    # Authentication
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],

    # Permissions
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],

    # Renderers
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],

    # Versioning
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],
    'VERSION_PARAM': 'version',

    # Throttling (Phase 1: Rate limiting)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',             # Anonymous users
        'user': '1000/hour',            # Authenticated users
        'login': '5/minute',            # Login attempts (brute force prevention)
        'content_creation': '20/hour',  # Create locations/reviews/comments
        'vote': '60/hour',              # Upvotes/downvotes
        'report': '10/hour',            # Content reports
    },
}

# =============================================================================
# CORS CONFIGURATION (Phase 2)
# =============================================================================

# CORS allowed origins (comma-separated in .env)
# Development: http://localhost:3000,http://localhost:8080
# Production: https://app.eventhorizon.com
CORS_ALLOWED_ORIGINS = [origin for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if origin]

# CORS security settings
CORS_ALLOW_CREDENTIALS = True       # Allow cookies/auth in CORS requests
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# =============================================================================
# CACHING
# =============================================================================

# Cache backend (required for rate limiting)
# Development: LocMemCache
# Production: Use Redis or Memcached
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# =============================================================================
# CRON JOBS
# =============================================================================

# Automated tasks via django-crontab
CRONJOBS = [
    # Commands:
    # python manage.py crontab show     - Show all cronjobs
    # python manage.py crontab add      - Add all cronjobs
    # python manage.py crontab remove   - Remove all cronjobs
]

# =============================================================================
# DEVELOPMENT SETTINGS
# =============================================================================

# Django Debug Toolbar (development only)
INTERNAL_IPS = ['127.0.0.1']

# =============================================================================
# MISCELLANEOUS
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
