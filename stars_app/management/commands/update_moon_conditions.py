from django.utils import timezone
from django.core.management.base import BaseCommand
from stars_app.models.viewinglocation import ViewingLocation
from stars_app.services.moon_service import MoonService

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update moon data values for all viewing locations'

    def add_arguments(self, parser):
        # Add option to force updates regardless of time
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update regardless of time of day',
        )

    def handle(self, *args, **options):
        moon_service = MoonService()
        locations = ViewingLocation.objects.all()
        updated_count = 0
        current_time = timezone.now()

        logger.info(f"Starting moon data update at {current_time}")

        for location in locations:
            try:
                # Check if it's night
                is_night = moon_service.get_is_nighttime(
                    location.latitude,
                    location.longitude,
                    current_time
                )

                # Get next twilight times
                twilight_times = moon_service.get_next_twilight_times(
                    location.latitude,
                    location.longitude,
                    current_time
                )

                if is_night or options.get('force', False):
                    # Calculate moon data for this specific location during the night
                    moon_data = moon_service.calculate_moon_data(
                        location.latitude,
                        location.longitude,
                        location.elevation,
                        current_time
                    )

                    # Update location with new moon data
                    location.moon_phase = moon_data['phase_percentage']
                    location.moon_altitude = moon_data['altitude']
                    location.moon_impact_score = moon_service.calculate_moon_impact(moon_data)
                    location.next_moonrise = moon_data['next_rise']
                    location.next_moonset = moon_data['next_set']
                    location.next_astronomical_dawn = twilight_times['next_sunrise']
                    location.next_astronomical_dusk = twilight_times['next_sunset']

                    # Save the updates
                    location.save(update_fields=[
                        'moon_phase', 'moon_altitude', 'moon_impact_score',
                        'next_moonrise', 'next_moonset',
                        'next_astronomical_dawn', 'next_astronomical_dusk'
                    ])

                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated moon data for {location.name} (Dark sky period)'
                        )
                    )
                else:
                    # During day, just update basic information
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping detailed update for {location.name} (Daylight period)'
                        )
                    )
                    moon_data = moon_service.calculate_moon_data(
                        location.latitude,
                        location.longitude,
                        location.elevation,
                        current_time
                    )

                    location.moon_phase = moon_data['phase_percentage']
                    location.save(update_fields=['moon_phase'])

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Failed to update moon data for location {location.name}: {str(e)}'
                    )
                )

        # Final success message with count
        logger.info(f"Moon data update completed successfully for {updated_count} locations.")
