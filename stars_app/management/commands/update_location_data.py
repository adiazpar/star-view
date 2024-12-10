from django.core.management.base import BaseCommand
from stars_app.models.viewinglocation import ViewingLocation


class Command(BaseCommand):
    help = 'Updates elevation and quality scores for all viewing locations'

    def handle(self, *args, **options):
        locations = ViewingLocation.objects.all()
        total = locations.count()

        self.stdout.write(f'Updating {total} locations...')

        for i, location in enumerate(locations, 1):
            self.stdout.write(f'Processing {i}/{total}: {location.name}')

            # Update elevation if needed
            if not location.elevation:
                location.update_elevation_from_mapbox()

            # Update quality score
            location.calculate_quality_score()

        self.stdout.write(self.style.SUCCESS('Successfully updated all locations'))