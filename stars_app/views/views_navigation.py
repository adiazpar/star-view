# ----------------------------------------------------------------------------------------------------- #
# This views_navigation.py file handles main navigation and public-facing views:                       #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides template views for the main application pages including the home page and interactive       #
# map. These views serve as the primary entry points for users to discover and explore stargazing      #
# locations.                                                                                            #
#                                                                                                       #
# Key Features:                                                                                         #
# - Home page: Landing page with upcoming events and location counts                                   #
# - Interactive map: Displays all stargazing locations on a map with custom tile server                #
# - Tile server configuration: Manages internal and public URLs for map tiles                          #
#                                                                                                       #
# Architecture:                                                                                         #
# - Function-based views for rendering templates                                                       #
# - Integrates with Mapbox for mapping functionality                                                   #
# - Uses custom tile server for map rendering                                                          #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import render
from django.conf import settings

# Model imports:
from stars_app.models.model_location import Location

# Other imports:
from datetime import datetime, timedelta


# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                  FUNCTION-BASED VIEWS                                                 #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

def home(request):
    """
    Display the home page with upcoming events and statistics.

    Shows the next celestial event, count of upcoming events, and count of
    nearby stargazing spots. This is the main landing page of the application.

    Args:
        request: HTTP request object

    Returns:
        Rendered home page template
    """
    # Example test event data (replace with actual event queries in the future)
    next_event = {
        'name': 'Lyrid Meteor Shower',
        'date': datetime.now() + timedelta(days=3, hours=14, minutes=22),
    }

    context = {
        'next_event': next_event,
        'upcoming_events_count': 12,  # Replace with actual query
        'nearby_spots_count': 8,  # Replace with actual query
    }

    return render(request, 'stars_app/home.html', context)


def map(request):
    """
    Display the interactive map with all stargazing locations.

    Shows all locations on an interactive map using Mapbox and a custom
    tile server. Users can browse locations geographically.

    Args:
        request: HTTP request object

    Returns:
        Rendered map page template
    """
    # Get all locations
    locations = Location.objects.all()

    # Get tile server configuration
    tile_config = get_tile_server_config()

    context = {
        'items': locations,
        'mapbox_token': settings.MAPBOX_TOKEN,
        'tile_server_url': tile_config['public_url'],
    }
    return render(request, 'stars_app/map.html', context)


def get_tile_server_config():
    """
    Get the tile server URL configuration for map rendering.

    Returns internal and public URLs for the custom tile server used
    to render map tiles.

    Returns:
        dict: Dictionary with 'internal_url' and 'public_url' keys
    """
    return {
        'internal_url': 'http://localhost:3001',
        'public_url': 'http://143.198.25.144:3001'
    }
