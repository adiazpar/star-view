from django.db import models


# Celestial Event Model --------------------------------------------- #
class CelestialEvent(models.Model):
    EVENT_TYPES = [
        ('METEOR', 'Meteor Shower'),
        ('ECLIPSE', 'Eclipse'),
        ('PLANET', 'Planetary Event'),
        ('AURORA', 'Aurora'),
        ('OTHER', 'Other'),
        ('COMET', 'Comet'),
    ]

    name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    description = models.TextField()

    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField(help_text="Elevation in meters")

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    viewing_radius = models.FloatField(help_text="Optimal viewing radius in km")

    def __str__(self):
        return f'{self.name} ({self.start_time.date()})'
