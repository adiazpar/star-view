# ----------------------------------------------------------------------------------------------------- #
# This views_navigation.py file handles main navigation and public-facing views:                        #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides template views for the main application pages including the home page and interactive        #
# map. These views serve as the primary entry points for users to discover and explore stargazing       #
# locations.                                                                                            #
#                                                                                                       #
# Key Features:                                                                                         #
# - Home page: Landing page with hero section and call-to-action buttons                                #
# - Interactive map: Displays all stargazing locations on a 3D globe using Mapbox                       #
# - Tile server integration: Uses custom tile server for map rendering (configured in settings)         #
#                                                                                                       #
# Architecture:                                                                                         #
# - Function-based views for rendering templates                                                        #
# - Integrates with Mapbox GL JS for 3D globe visualization                                             #
# - Uses settings.TILE_SERVER_URL for deployment flexibility                                            #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import render
from django.conf import settings

# Model imports:
from stars_app.models.model_location import Location



# ----------------------------------------------------------------------------- #
# Display the home page with hero section and call-to-action.                   #
#                                                                               #
# Main landing page that introduces users to the application and provides       #
# navigation options to explore the map or access their favorites.              #
#                                                                               #
# Args:     request: HTTP request object                                        #
# Returns:  Rendered home page template                                         #
# ----------------------------------------------------------------------------- #
def home(request):
    return render(request, 'stars_app/home/home_base.html')


# ----------------------------------------------------------------------------- #
# Display the interactive 3D map with all stargazing locations.                 #
#                                                                               #
# Renders all locations on a 3D globe using Mapbox GL JS with custom tile       #
# server for map rendering. Users can browse locations geographically and       #
# filter by favorites.                                                          #
#                                                                               #
# Args:     request: HTTP request object                                        #
# Returns:  Rendered map page template with locations and configuration         #
# ----------------------------------------------------------------------------- #
def map(request):
    # Get all locations for the sidebar list
    locations = Location.objects.all()

    context = {
        'items': locations,
        'mapbox_token': settings.MAPBOX_TOKEN,
        'tile_server_url': settings.TILE_SERVER_URL,
    }
    return render(request, 'stars_app/map/map_base.html', context)
