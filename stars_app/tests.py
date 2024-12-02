from django.test import TestCase, Client
from stars_app.models import CelestialEvent, ViewingLocation
from django.utils import timezone
from django.urls import reverse
from .models import User, ViewingLocation, CelestialEvent
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta


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

class ViewingLocationViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.force_authenticate(user=self.user)
        
        self.viewing_location = ViewingLocation.objects.create(
            name="Mountain Peak",
            latitude=39.7392,
            longitude=-104.9903,
            elevation=4300,
            light_pollution_value=3,
            quality_score=85,
            added_by=self.user
        )

    def test_list_viewing_locations(self):
        url = reverse('viewing-locations-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Mountain Peak')

    def test_create_viewing_location(self):
        url = reverse('viewing-locations-list')
        data = {
            "name": "Hilltop",
            "latitude": 38.8951,
            "longitude": -77.0364,
            "elevation": 300,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ViewingLocation.objects.count(), 2)

    def test_viewing_location_detail(self):
        url = reverse('viewing-locations-detail', args=[self.viewing_location.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Mountain Peak')

class CelestialEventViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.force_authenticate(user=self.user)
        
        self.event = CelestialEvent.objects.create(
            name="Lunar Eclipse",
            event_type="ECLIPSE",
            description="A total lunar eclipse",
            latitude=34.0522,
            longitude=-118.2437,
            elevation=305,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            viewing_radius=100
        )

    def test_list_celestial_events(self):
        url = reverse('celestial-events-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Lunar Eclipse')

    def test_create_celestial_event(self):
        url = reverse('celestial-events-list')
        data = {
            "name": "Meteor Shower",
            "event_type": "METEOR",
            "description": "Annual meteor shower",
            "latitude": 36.7783,
            "longitude": -119.4179,
            "elevation": 200,
            "start_time": (timezone.now() + timedelta(days=1)).isoformat(),
            "end_time": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
            "viewing_radius": 150
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CelestialEvent.objects.count(), 2)

    def test_celestial_event_detail(self):
        url = reverse('celestial-events-detail', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Lunar Eclipse')

