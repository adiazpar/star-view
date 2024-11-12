import os
import sys

# Add the project root to the Python path
sys.path.append('/environment/Group8-fall2024')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

import django
django.setup()  # Initialize Django

from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.db.models import Q
from django.contrib.auth.models import User
from stars_app.models import FavoriteLocation, ViewingLocation, CelestialEvent

def get_favorites_and_events():
    # Use timezone-aware datetimes
    now = make_aware(datetime.now())
    future = now + timedelta(days=30)

    # Query upcoming events within the timezone-aware range
    upcoming_events = CelestialEvent.objects.filter(
        Q(start_time__gte=now) & Q(start_time__lte=future)
    )

    # Existing logic for users and events
    users = User.objects.all()
    for user in users:
        print(f"User: {user.username} ({user.email})")

        favorite_locations = FavoriteLocation.objects.filter(user=user)
        if favorite_locations.exists():
            print("  Favorite Locations:")
            for fav in favorite_locations:
                print(f"    - {fav.location.name} ({fav.location.latitude}, {fav.location.longitude})")

        user_events = upcoming_events.filter(
            Q(latitude__in=[fav.location.latitude for fav in favorite_locations]) &
            Q(longitude__in=[fav.location.longitude for fav in favorite_locations])
        )

        if user_events.exists():
            print("  Upcoming Events:")
            for event in user_events:
                print(f"    - {event.name} ({event.start_time} - {event.end_time})")
        else:
            print("  No upcoming events.")

if __name__ == "__main__":
    get_favorites_and_events()

