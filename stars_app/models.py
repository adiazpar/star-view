from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
import os

# Create your models here.

class Forecast(models.Model):
    createTime = models.DateTimeField(auto_now=True) #when model is created or updated get new time 
    forecast = models.JSONField(default=list, null=True)

def defaultforecast():
    tmp = Forecast.objects.create()
    return tmp.id

# Viewing Location Model -------------------------------------------- #
class ViewingLocation(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField(help_text="Elevation in meters")
    
    forecast = models.ForeignKey(Forecast, on_delete=models.CASCADE, default=defaultforecast) 
    cloudCoverPercentage = models.FloatField(null=True)

    light_pollution_value = models.FloatField(null=True, blank=True, help_text="Calculated light pollution value from tiles")
    quality_score = models.FloatField(null=True, blank=True)

    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def getForecast(self):
        #will eventually actually get a forecast
        return [0.71, 0.32, 0.53]

    def updateForecast(self):
        if (len(self.forecast.forecast) == 0):
            self.forecast.forecast = self.getForecast()
        currentTime = timezone.make_aware(datetime.datetime.now())
        beginTime = self.forecast.createTime
        dateDelta = currentTime - beginTime
        days, seconds = dateDelta.days, dateDelta.seconds
        hours = int(days * 24 + seconds // 3600)
        if hours > len(self.forecast.forecast):
            self.forecast.forecast = self.getForecast()
            self.forecast.save()
            self.updateForecast()
        self.cloudCoverPercentage = self.forecast.forecast[hours]
        self.forecast.save()

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updateForecast() 
# Favorite Location Model ------------------------------------------- #
class FavoriteLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_locations')
    location = models.ForeignKey(ViewingLocation, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # This makes sure a user can't favorite the same location multiple times:
        unique_together = ['user', 'location']

    def __str__(self):
        return f'{self.user.username} - {self.location.name}'


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

