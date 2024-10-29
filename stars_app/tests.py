from django.test import TestCase, Client
from stars_app.models import CelestialEvent, ViewingLocation
from django.utils import timezone
from django.urls import reverse
from .models import User

class ViewingLocationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        login = self.client.login(username='testuser', password='12345')
        ViewingLocation.objects.create(name="Test Location", latitude=1.1, longitude=1.1, elevation=1.1, light_pollution_value=1.1,quality_score=1.1,added_by=self.user,created_at=timezone.now())
    
    def test_Location(self):
        test_location = ViewingLocation.objects.get(name="Test Location")

        assert test_location.name == "Test Location"
        assert test_location.latitude == 1.1
        assert test_location.longitude == 1.1
        assert test_location.elevation == 1.1
        assert test_location.light_pollution_value == 1.1
        assert test_location.quality_score == 1.1
        assert test_location.added_by == self.user

class CelestialEventTest(TestCase):
    def setUp(self):
        self.test_time = timezone.now()
        self.user = User.objects.create_user(username='testuser', password='12345')
        login = self.client.login(username='testuser', password='12345')
        ViewingLocation.objects.create(name="Test Location", latitude=1.1, longitude=1.1, elevation=1.1, light_pollution_value=1.1,quality_score=1.1,added_by=self.user,created_at=timezone.now())
        event = CelestialEvent.objects.create(name="Test Comet", event_type="Comet", description="Test", latitude=1.1, longitude=1.1, elevation=1.1, start_time=self.test_time, end_time=self.test_time, viewing_radius=100)

    def test_Event(self):
        test_event = CelestialEvent.objects.get(name="Test Comet")

        assert test_event.name == "Test Comet"
        assert test_event.event_type == "Comet"
        assert test_event.description == "Test"
        assert test_event.latitude == 1.1
        assert test_event.longitude == 1.1
        assert test_event.elevation == 1.1
        assert test_event.start_time == self.test_time
        assert test_event.end_time == self.test_time
        assert test_event.viewing_radius == 100

class URLTest(TestCase):
    def test_urls(self):

        url = reverse("home")
        response = self.client.get(url)
        assert response.status_code == 200

        url = reverse("map")
        response = self.client.get(url)
        assert response.status_code == 200

        url = reverse("event_list")
        response = self.client.get(url)
        assert response.status_code == 200

        url = reverse("register")
        response = self.client.get(url)
        assert response.status_code == 200

        url = reverse("login")
        response = self.client.get(url)
        assert response.status_code == 200

        url = reverse("logout")
        response = self.client.get(url)
        assert response.status_code == 302 # Redirects