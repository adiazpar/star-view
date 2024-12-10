from django.core.management.base import BaseCommand
from stars_app.models.viewinglocation import ViewingLocation
from stars_app.services.light_pollution import LightPollutionService

class Command(BaseCommand):
    help = 'Update light pollution values for all viewing locations'

    def handle(self, *args, **options):
        service = LightPollutionService()
        locations = ViewingLocation.objects.all()

        self.stdout.write('Updating light pollution values...')

        for location in locations:
            light_pollution = service.get_light_pollution(
                location.latitude,
                location.longitude
            )

            if light_pollution is not None:
                location.light_pollution_value = light_pollution
                location.quality_score = service.calculate_quality_score(light_pollution)
                location.save(update_fields=['light_pollution_value', 'quality_score'])

        self.stdout.write(self.style.SUCCESS('Successfully updated light pollution values'))