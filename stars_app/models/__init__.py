# ----------------------------------------------------------------------------------------------------- #
# This __init__.py file marks the models directory as a Python package and exposes all models:          #
#                                                                                                       #
# Purpose:                                                                                              #
# This file imports all model classes and makes them available at the package level. This allows        #
# cleaner imports throughout the application (e.g., `from stars_app.models import Location` instead     #
# of `from stars_app.models.model_location import Location`).                                           #
#                                                                                                       #
# Model Organization:                                                                                   #
# Models are separated into individual files for better organization and maintainability:               #
#                                                                                                       #
# Signal Registration:                                                                                  #
# The final import statement loads signals.py to ensure signal handlers (@receiver decorators) are      #
# registered for automatic file cleanup when models are deleted.                                        #
#                                                                                                       #
# Django Integration:                                                                                   #
# Django automatically discovers models in any module listed in __all__ or imported in __init__.py.     #
# All models imported here are automatically registered with Django's ORM and available for             #
# migrations, admin, and queries.                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# Location models:
from .model_location import Location
from .model_location_favorite import FavoriteLocation

# User models:
from .model_user_profile import UserProfile

# Review models:
from .model_review import Review
from .model_review_comment import ReviewComment
from .model_review_photo import ReviewPhoto

# Generic models (ContentTypes framework):
from .model_report import Report
from .model_vote import Vote

# Audit/Security models:
from .model_audit_log import AuditLog

# Import signals to ensure they're registered:
from stars_app.utils import signals