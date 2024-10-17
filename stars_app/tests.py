from django.test import TestCase
from stars_app.models import Event, Location
from django.utils import timezone

class LocationTest(TestCase):
    def setUp(self):
        Location.objects.create(location_name="Test Location", zip_code=80808, latitude=1.1, latitude_direction="N", longitude=1.1, longitude_direction="W")
    
    def test_Location(self):
        test_location = Location.objects.get(location_name="Test Location")

        assert test_location.location_name == "Test Location"
        assert test_location.zip_code == 80808
        assert test_location.latitude == 1.1
        assert test_location.latitude_direction == "N"
        assert test_location.longitude == 1.1
        assert test_location.longitude_direction == "W"

class EventTest(TestCase):
    peak = timezone.now()
    def setUp(self):
        event_location = Location.objects.create(location_name="Test Location", zip_code=80808, latitude=1.1, latitude_direction="N", longitude=1.1, longitude_direction="W")
        event = Event.objects.create(name="Test Comet", event_type="Comet", viewing_radius=100, peak_time=self.peak, location=event_location)

    def test_Event(self):
        test_event = Event.objects.get(name="Test Comet")

        assert test_event.name == "Test Comet"
        assert test_event.event_type == "Comet"
        assert test_event.viewing_radius == 100
        assert test_event.peak_time == self.peak
        assert test_event.location.location_name == "Test Location"
        assert test_event.location.zip_code == 80808
        assert test_event.location.latitude == 1.1
        assert test_event.location.latitude_direction == "N"
        assert test_event.location.longitude == 1.1
        assert test_event.location.longitude_direction == "W"