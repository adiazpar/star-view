from rest_framework import serializers
from .models import ViewingLocation, FavoriteLocation, CelestialEvent


# Viewing Location Serializer --------------------------------------- #
class ViewingLocationSerializer(serializers.ModelSerializer):
    added_by = serializers.ReadOnlyField(source='added_by.username')
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = ViewingLocation
        fields = ['id', 'name', 'latitude', 'longitude', 'elevation',
                 'light_pollution_value', 'quality_score', 'added_by',
                  'created_at', 'is_favorited']
        read_only_fields = ['light_pollution_value', 'quality_score', 'added_by', 'created_at']

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteLocation.objects.filter(
                user=request.user,
                location=obj
            ).exists()

        # Otherwise return false since no favorites:
        return False


# Celestial Event Serializer ---------------------------------------- #
class CelestialEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CelestialEvent
        fields = ['id', 'name', 'event_type', 'description',
                  'latitude', 'longitude', 'elevation',
                  'start_time', 'end_time',
                  'viewing_radius']