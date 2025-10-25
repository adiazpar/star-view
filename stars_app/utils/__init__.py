# ----------------------------------------------------------------------------------------------------- #
# This __init__.py file marks the utils directory as a Python package and exposes utility modules:      #
#                                                                                                       #
# Purpose:                                                                                              #
# Centralizes reusable utility code that provides cross-cutting functionality across stars_app.         #
# These utilities handle validation, rate limiting, and signal handling - concerns that span multiple   #
# parts of the application (models, views, serializers).                                                #
#                                                                                                       #
# Why This Directory Exists:                                                                            #
# - Prevents circular imports between models/views/serializers                                          #
# - Follows Django convention for organizing utility modules                                            #
# - Enables clean imports: `from stars_app.utils import validate_image_file`                            #
# - Groups related functionality (security validators, throttles, signals)                              #
#                                                                                                       #
# Modules in This Package:                                                                              #
# - validators.py: File upload validation, coordinate validation, XSS sanitization                      #
# - throttles.py: DRF rate limiting classes (login, content creation, voting, reporting)                #
# - signals.py: Django signal handlers (file cleanup, aggregate updates)                                #
#                                                                                                       #
# Note on signals.py:                                                                                   #
# The signals module is NOT imported here to avoid circular imports (signals imports models, models     #
# import validators from utils). Signal handlers are automatically registered via AppConfig.ready().    #
# ----------------------------------------------------------------------------------------------------- #

# Import all validators
from .validators import (
    validate_file_size,
    validate_image_file,
    sanitize_html,
    sanitize_plain_text,
    validate_latitude,
    validate_longitude,
    validate_elevation,
)

# Import all throttle classes
from .throttles import (
    LoginRateThrottle,
    ContentCreationThrottle,
    VoteThrottle,
    ReportThrottle,
)

__all__ = [
    # Validators
    'validate_file_size',
    'validate_image_file',
    'sanitize_html',
    'sanitize_plain_text',
    'validate_latitude',
    'validate_longitude',
    'validate_elevation',

    # Throttles
    'LoginRateThrottle',
    'ContentCreationThrottle',
    'VoteThrottle',
    'ReportThrottle',
]
