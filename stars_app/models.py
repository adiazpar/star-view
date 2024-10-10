from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=30)
    event_type = models.CharField(max_length=30)
    viewing_radius = models.IntegerField(default=10)
    peak_time = models.DateTimeField(default=timezone.now())
    location = models.ForeignKey(Location, on_delete=models.CASCADE)

class Location(models.Model):
    location_name = models.CharField(max_length=30)
    zip_code = models.IntegerField(default=00000)
    latitude = models.FloatField()
    latitude_direction = models.CharField(max_length=1)
    longitude = models.FloatField()
    longitude_direction = models.CharField(max_length=1)