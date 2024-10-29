from rest_framework import serializers
from .models import ViewingLocation, CelestialEvent, EventLocation

class ViewingLocationSerializer(serializers.ModelSerializer):
    added_by = serializers.ReadOnlyField(source='added_by.username')

    class Meta:
        model = ViewingLocation
        fields = ['id', 'name', 'latitude', 'longitude', 'elevation',
                 'light_pollution_value', 'quality_score', 'added_by', 'created_at']
        read_only_fields = ['light_pollution_value', 'quality_score', 'added_by', 'created_at']


class CelestialEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CelestialEvent
        fields = ['id', 'name', 'event_type', 'start_time', 'end_time',
                 'description', 'viewing_radius', 'location']


class EventLocationSerializer(serializers.ModelSerializer):
    location = ViewingLocationSerializer(read_only=True)
    event = CelestialEventSerializer(read_only=True)

    class Meta:
        model = EventLocation
        fields = ['id', 'event', 'location', 'notes']