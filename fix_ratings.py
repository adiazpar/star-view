"""
Run this in Django shell to update rating statistics:
python manage.py shell < fix_ratings.py

OR copy and paste this code into: python manage.py shell
"""

from stars_app.models.viewinglocation import ViewingLocation
from django.db.models import Avg, Count

print("Updating rating statistics for all locations...")

locations = ViewingLocation.objects.all()
updated_count = 0

for location in locations:
    # Get review stats
    review_stats = location.reviews.aggregate(
        count=Count('id'),
        avg_rating=Avg('rating')
    )

    rating_count = review_stats['count'] or 0
    average_rating = round(review_stats['avg_rating'], 2) if review_stats['avg_rating'] else 0

    # Update if values changed
    if location.rating_count != rating_count or float(location.average_rating) != average_rating:
        location.rating_count = rating_count
        location.average_rating = average_rating
        location.save(update_fields=['rating_count', 'average_rating'])
        updated_count += 1
        print(f"  Updated {location.name}: {rating_count} reviews, avg rating {average_rating}")

print(f"\nComplete! Updated {updated_count} locations.")
print(f"Locations with reviews: {ViewingLocation.objects.filter(rating_count__gt=0).count()}")
