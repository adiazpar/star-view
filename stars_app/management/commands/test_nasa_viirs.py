from django.core.management.base import BaseCommand
from stars_app.services.light_pollution import LightPollutionService
from stars_app.models.viewinglocation import ViewingLocation
import json

class Command(BaseCommand):
    help = 'Test NASA VIIRS Black Marble coordinate-based light pollution estimation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lat',
            type=float,
            default=39.7392,  # Denver, CO
            help='Latitude to test (default: Denver, CO)'
        )
        parser.add_argument(
            '--lon',
            type=float,
            default=-104.9903,  # Denver, CO
            help='Longitude to test (default: Denver, CO)'
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear light pollution cache before testing'
        )
        parser.add_argument(
            '--update-all',
            action='store_true',
            help='Update light pollution for all existing locations'
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Show detailed debug information'
        )

    def handle(self, *args, **options):
        service = LightPollutionService()
        
        self.stdout.write(
            self.style.SUCCESS('NASA VIIRS Black Marble Light Pollution Test')
        )
        self.stdout.write("=" * 50)
        
        # Clear cache if requested
        if options['clear_cache']:
            self.stdout.write("Clearing light pollution cache...")
            if service.clear_cache():
                self.stdout.write(
                    self.style.SUCCESS("✓ Cache cleared successfully")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("✗ Failed to clear cache")
                )
            self.stdout.write("")

        # Test specific coordinates
        lat = options['lat']
        lon = options['lon']
        
        self.stdout.write(f"Testing coordinates: {lat}, {lon}")
        
        if options['debug']:
            # Get detailed debug information
            debug_info = service.get_debug_info(lat, lon)
            self.stdout.write("\nDEBUG INFORMATION:")
            self.stdout.write("-" * 30)
            self.stdout.write(json.dumps(debug_info, indent=2, default=str))
            self.stdout.write("")

        # Test the main API call
        self.stdout.write("Fetching light pollution data...")
        try:
            light_pollution = service.get_light_pollution(lat, lon)
            quality_score = service.calculate_quality_score(light_pollution)
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ Light Pollution: {light_pollution} mag/arcsec²")
            )
            self.stdout.write(
                self.style.SUCCESS(f"✓ Quality Score: {quality_score}/100")
            )
            
            # Interpret the results
            if light_pollution > 21.0:
                rating = "Excellent (Dark Sky)"
            elif light_pollution > 20.0:
                rating = "Very Good (Rural)"
            elif light_pollution > 19.0:
                rating = "Good (Suburban)"
            elif light_pollution > 18.0:
                rating = "Fair (Urban)"
            else:
                rating = "Poor (City Center)"
                
            self.stdout.write(f"  Sky Quality: {rating}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Error: {str(e)}")
            )

        # Update all locations if requested
        if options['update_all']:
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("Updating all existing locations...")
            
            locations = ViewingLocation.objects.all()
            total_locations = locations.count()
            updated_count = 0
            failed_count = 0
            
            for i, location in enumerate(locations):
                self.stdout.write(
                    f"Updating {i+1}/{total_locations}: {location.name}...",
                    ending=""
                )
                
                try:
                    if location.update_light_pollution():
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f" ✓ {location.light_pollution_value} mag/arcsec²")
                        )
                    else:
                        failed_count += 1
                        self.stdout.write(
                            self.style.WARNING(" ! No data available")
                        )
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f" ✗ Error: {str(e)}")
                    )
            
            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS(f"Updated: {updated_count} locations")
            )
            if failed_count > 0:
                self.stdout.write(
                    self.style.WARNING(f"Failed: {failed_count} locations")
                )

        # Show system information
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SYSTEM INFORMATION:")
        self.stdout.write("-" * 20)
        self.stdout.write("Current Implementation:")
        self.stdout.write("  ✓ NASA VIIRS Black Marble coordinate-based estimation")
        self.stdout.write("  ✓ City proximity database with real radiance values")
        self.stdout.write("  ✓ Geographic region fallback estimation")
        self.stdout.write("")
        self.stdout.write("Data Sources:")
        self.stdout.write("  • NASA VIIRS Black Marble (VNP46A1) city database")
        self.stdout.write("  • Geographic coordinate pattern analysis")
        self.stdout.write("  • 7-day caching for performance")
        self.stdout.write("")
        self.stdout.write("Test Commands:")
        self.stdout.write("  python manage.py test_nasa_viirs --debug")
        self.stdout.write("  python manage.py test_nasa_viirs --lat 40.7580 --lon -73.9855")
        self.stdout.write("  python manage.py test_nasa_viirs --update-all --clear-cache")
        self.stdout.write("")
        self.stdout.write("Next Steps:")
        self.stdout.write("  • Ready for NASA EarthData Login integration")
        self.stdout.write("  • All deprecated NASA API key code removed") 