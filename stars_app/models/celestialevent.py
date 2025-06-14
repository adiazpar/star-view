from django.db import models
from .base import CelestialEventBase
from stars_app.managers import CelestialEventManager


# Celestial Event Model --------------------------------------------- #
class CelestialEvent(CelestialEventBase):
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

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    viewing_radius = models.FloatField(help_text="Optimal viewing radius in km")

    # Custom manager
    objects = models.Manager()
    events = CelestialEventManager()

    class Meta:
        indexes = [
            models.Index(fields=['event_type'], name='event_type_idx'),
            models.Index(fields=['start_time'], name='start_time_idx'),
            models.Index(fields=['end_time'], name='end_time_idx'),
            models.Index(fields=['latitude', 'longitude'], name='event_coords_idx'),
        ]
        ordering = ['start_time']

    def __str__(self):
        return f'{self.name} ({self.start_time.date()})'
