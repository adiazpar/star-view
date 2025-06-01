from django.db.models import Avg
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from stars_app.models.forecast import Forecast
from stars_app.models.viewinglocation import ViewingLocation
from stars_app.models.locationreview import LocationReview
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

import requests
from django_project import settings


# NASA API key tests removed - using coordinate-based estimation instead
# For light pollution testing, use: python manage.py test_nasa_viirs --debug
