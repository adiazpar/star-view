from rest_framework import serializers
from .models import Location, Event

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['location_name', 'zip_code', 'latitude', 'latitude_direction', 'longitude', 'longitude_direction']

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['name', 'event_type', 'viewing_radius', 'peak_time', 'location']