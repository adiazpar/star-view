from django.core.management.base import BaseCommand
from stars_app.models.viewinglocation import ViewingLocation
import time


class Command(BaseCommand):
    help = 'Updates elevation data for all viewing locations'

    def handle(self, *args, **options):
        locations = ViewingLocation.objects.all()
        total = locations.count()
        updated = 0

        self.stdout.write(f'Updating elevation for {total} locations...')

        for i, location in enumerate(locations, 1):
            self.stdout.write(f'Processing {i}/{total}: {location.name}')

            if location.update_elevation_from_mapbox():
                updated += 1
                location.calculate_quality_score()  # Update quality score with new elevation

            # Add a small delay to avoid rate limiting
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully updated elevation for {updated} out of {total} locations'
        ))