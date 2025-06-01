# docker_settings.py
# Minimal Docker-specific settings that inherit from your existing settings.py
# This approach preserves all your existing configuration while adding Docker optimizations

from django_project.settings import *  # Import everything from your existing settings

# Override only what's needed for Docker static file serving
DEBUG = True  # Ensure debug mode for development container

# Add WhiteNoise to the beginning of middleware for static file serving
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE

# WhiteNoise configuration for development
WHITENOISE_USE_FINDERS = True  # Let WhiteNoise find static files during development
WHITENOISE_AUTOREFRESH = True  # Automatically reload CSS changes

# Ensure static files are served properly in container
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Docker-specific host configuration
ALLOWED_HOSTS = ALLOWED_HOSTS + ['webapp', 'tile-server']  # Add container hostnames

# Container-specific paths
# We're keeping your existing STATIC_URL, STATIC_ROOT, and STATICFILES_DIRS

# Tile Server Configuration
TILE_SERVER_INTERNAL_URL = os.getenv('TILE_SERVER_URL', 'http://tile-server:3001')  # For server-to-server communication
TILE_SERVER_PUBLIC_URL = os.getenv('TILE_SERVER_PUBLIC_URL', 'http://localhost:3001')  # For browser access

ALLOWED_HOSTS = ALLOWED_HOSTS + ['127.0.0.1', '0.0.0.0']

CORS_ALLOW_ALL_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

# Optional: Add some debugging for static files during development
if DEBUG:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Static files configuration:")
    logger.info(f"  STATIC_URL: {STATIC_URL}")
    logger.info(f"  STATIC_ROOT: {STATIC_ROOT}")
    logger.info(f"  STATICFILES_DIRS: {STATICFILES_DIRS}")
    logger.info(f"  BASE_DIR: {BASE_DIR}")