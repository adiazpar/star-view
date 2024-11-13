from django.core.management.base import BaseCommand
from stars_app.services import AuroraService, MeteorShowerService, CometService, EclipseService
from stars_app.models import CelestialEvent


class Command(BaseCommand):
    help = 'Updates celestial events'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['aurora', 'meteor', 'comet', 'eclipse', 'all'],
            default='all',
            help='Specify event type to update: "aurora", "meteor", "comet", "eclipse", or "all"'
        )

    def handle(self, *args, **kwargs):
        event_type = kwargs['type']

        # Clear events based on type
        self.clear_events(event_type)

        # Update events
        if event_type in ['all', 'aurora']:
            self.update_aurora_events()

        if event_type in ['all', 'meteor']:
            self.update_meteor_events()

        if event_type in ['all', 'comet']:
            self.update_comet_events()

        if event_type in ['all', 'eclipse']:
            self.update_eclipse_events()

        # Final report
        self.print_event_counts()

    def clear_events(self, event_type):
        """Clear events based on type"""
        if event_type == 'all':
            # Clear all event types
            deleted_count = CelestialEvent.objects.all().delete()
            self.stdout.write(f"Cleared all existing events")
        else:
            # Clear only specified event type
            deleted_count = CelestialEvent.objects.filter(event_type=event_type.upper()).delete()
            self.stdout.write(f"Cleared existing {event_type} events")

    def update_aurora_events(self):
        """Update aurora events"""
        try:
            service = AuroraService()
            service.fetch_aurora_events()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating aurora events: {str(e)}')
            )

    def update_meteor_events(self):
        """Update meteor events"""
        try:
            service = MeteorShowerService()
            service.update_meteor_showers()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating meteor events: {str(e)}')
            )

    def update_comet_events(self):
        """Update comet events"""
        try:
            service = CometService()
            service.update_comets()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating comet events: {str(e)}')
            )

    def update_eclipse_events(self):
        """Update eclipse events"""
        try:
            service = EclipseService()
            service.update_eclipses()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating eclipse events: {str(e)}')
            )

    def print_event_counts(self):
        """Print final counts of all event types"""
        aurora_count = CelestialEvent.objects.filter(event_type='AURORA').count()
        meteor_count = CelestialEvent.objects.filter(event_type='METEOR').count()
        comet_count = CelestialEvent.objects.filter(event_type='COMET').count()
        eclipse_count = CelestialEvent.objects.filter(event_type='ECLIPSE').count()

        self.stdout.write('\nFinal Event Counts:')
        self.stdout.write(f'Aurora Events: {aurora_count}')
        self.stdout.write(f'Meteor Events: {meteor_count}')
        self.stdout.write(f'Comet Events: {comet_count}')
        self.stdout.write(f'Eclipse Events: {eclipse_count}')
        self.stdout.write(
            self.style.SUCCESS(
                f'Total Events: {aurora_count + meteor_count + comet_count + eclipse_count}'
            )
        )