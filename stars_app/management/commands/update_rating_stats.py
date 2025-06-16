from django.core.management.base import BaseCommand
from django.db.models import Avg
from stars_app.models import ViewingLocation


class Command(BaseCommand):
    help = 'Update rating statistics for all locations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--location-id',
            type=int,
            help='Update rating stats for a specific location ID only',
        )

    def handle(self, *args, **options):
        location_id = options.get('location_id')
        
        if location_id:
            locations = ViewingLocation.objects.filter(id=location_id)
            if not locations.exists():
                self.stdout.write(
                    self.style.ERROR(f'Location with ID {location_id} not found')
                )
                return
        else:
            locations = ViewingLocation.objects.all()

        updated_count = 0
        
        for location in locations:
            # Get all reviews for this location
            reviews = location.reviews.all()
            
            # Update rating count
            old_count = location.rating_count
            old_avg = location.average_rating
            
            location.rating_count = reviews.count()
            
            # Calculate and update average rating
            if location.rating_count > 0:
                avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
                location.average_rating = round(avg_rating, 2) if avg_rating else 0
            else:
                location.average_rating = 0
            
            # Only save if something changed
            if (old_count != location.rating_count or 
                old_avg != location.average_rating):
                location.save(update_fields=['rating_count', 'average_rating'])
                updated_count += 1
                
                self.stdout.write(
                    f'Updated {location.name}: '
                    f'{old_count} -> {location.rating_count} reviews, '
                    f'{old_avg} -> {location.average_rating} avg rating'
                )

        if updated_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All location rating statistics are already up to date')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated rating statistics for {updated_count} locations')
            )