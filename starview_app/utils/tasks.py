# ----------------------------------------------------------------------------------------------------- #
# This tasks.py file defines Celery tasks for asynchronous background processing:                       #
#                                                                                                       #
# Purpose:                                                                                              #
# Handles time-consuming operations asynchronously to improve user experience and application           #
# responsiveness. Users get instant feedback while heavy operations run in the background.              #
#                                                                                                       #
# Key Tasks:                                                                                            #
# - enrich_location_data: Fetches address and elevation from Mapbox (2-5 seconds)                       #
# - Future tasks: Bulk email sending, image processing, data exports, report generation                 #
#                                                                                                       #
# Architecture:                                                                                         #
# - Tasks are queued in Redis broker when triggered                                                     #
# - Celery worker processes tasks in background                                                         #
# - Results stored in Redis (expire after 1 hour)                                                       #
# - Location model calls .delay() to trigger async execution                                            #
#                                                                                                       #
# Usage:                                                                                                #
# Synchronous:  enrich_location_data(location_id)           # Blocks until complete                     #
# Asynchronous: enrich_location_data.delay(location_id)     # Returns immediately                       #
# ----------------------------------------------------------------------------------------------------- #

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

# Get Celery logger (integrates with Celery's logging system)
logger = get_task_logger(__name__)


# ----------------------------------------------------------------------------- #
# Enriches a location with address and elevation data from Mapbox.              #
#                                                                               #
# This task runs asynchronously in the background, allowing location creation   #
# to return instantly to the user. The location starts with basic data          #
# (name, coordinates) and is enriched with address/elevation a few seconds      #
# later.                                                                        #
#                                                                               #
# Args:                                                                         #
#   location_id (int): The ID of the Location object to enrich                  #
#                                                                               #
# Returns:                                                                      #
#   dict: Success status and enriched fields                                    #
#                                                                               #
# Task Settings:                                                                #
#   - bind=True: Task instance passed as first arg (enables self.retry())       #
#   - max_retries=3: Retry up to 3 times on failure                             #
#   - default_retry_delay=60: Wait 60 seconds between retries                   #
#                                                                               #
# Error Handling:                                                               #
#   - If Mapbox API fails, task retries up to 3 times                           #
#   - If location not found (deleted), task fails gracefully                    #
#   - Logs all operations for monitoring and debugging                          #
# ----------------------------------------------------------------------------- #
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def enrich_location_data(self, location_id):
    """
    Asynchronously enriches a location with address and elevation data from Mapbox.

    This task is triggered after a location is created, allowing the user to get
    an instant response while the enrichment happens in the background.
    """
    from starview_app.models import Location
    from starview_app.services.location_service import LocationService

    logger.info(f"Starting enrichment for location ID: {location_id}")

    try:
        # Get the location object
        location = Location.objects.get(id=location_id)

        # Skip if external APIs are disabled (testing mode)
        if getattr(settings, 'DISABLE_EXTERNAL_APIS', False):
            logger.info(f"Skipping enrichment for location {location_id} (APIs disabled)")
            return {
                'status': 'skipped',
                'location_id': location_id,
                'reason': 'DISABLE_EXTERNAL_APIS is True'
            }

        # Track which fields were successfully enriched
        enriched_fields = []

        # Enrich address from coordinates
        try:
            address_success = LocationService.update_address_from_coordinates(location)
            if address_success:
                enriched_fields.append('address')
                logger.info(f"Address enriched for location {location_id}: {location.formatted_address}")
            else:
                logger.warning(f"Address enrichment failed for location {location_id}")
        except Exception as e:
            logger.error(f"Error enriching address for location {location_id}: {str(e)}")
            # Don't fail the entire task if address fails, continue to elevation

        # Enrich elevation from Mapbox
        try:
            elevation_success = LocationService.update_elevation_from_mapbox(location)
            if elevation_success:
                enriched_fields.append('elevation')
                logger.info(f"Elevation enriched for location {location_id}: {location.elevation}m")
            else:
                logger.warning(f"Elevation enrichment failed for location {location_id}")
        except Exception as e:
            logger.error(f"Error enriching elevation for location {location_id}: {str(e)}")

        # Return success with enriched fields
        result = {
            'status': 'success',
            'location_id': location_id,
            'location_name': location.name,
            'enriched_fields': enriched_fields,
            'formatted_address': location.formatted_address,
            'elevation': location.elevation
        }

        logger.info(f"Enrichment complete for location {location_id}: {enriched_fields}")
        return result

    except Location.DoesNotExist:
        # Location was deleted before enrichment could complete
        logger.error(f"Location {location_id} not found - may have been deleted")
        return {
            'status': 'error',
            'location_id': location_id,
            'error': 'Location not found (may have been deleted)'
        }

    except Exception as exc:
        # Unexpected error - retry the task
        logger.error(f"Unexpected error enriching location {location_id}: {str(exc)}")

        # Retry the task (up to max_retries times)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for location {location_id}")
            return {
                'status': 'failed',
                'location_id': location_id,
                'error': f'Max retries exceeded: {str(exc)}'
            }


# ----------------------------------------------------------------------------- #
# Example task for testing Celery setup.                                        #
#                                                                               #
# Usage:                                                                        #
#   from starview_app.utils.tasks import test_celery                               #
#   result = test_celery.delay("Hello from Celery!")                            #
#   print(result.get(timeout=10))  # Wait up to 10 seconds for result           #
# ----------------------------------------------------------------------------- #
@shared_task
def test_celery(message):
    logger.info(f"Test task received message: {message}")
    return f"Task completed successfully: {message}"
