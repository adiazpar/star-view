"""
Pytest configuration and fixtures for Event Horizon project.
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture
def api_client():
    """Provide a Django test client for API testing."""
    return Client()


@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(user):
    """Provide an authenticated test client."""
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def sample_location_data():
    """Provide sample viewing location data for testing."""
    return {
        'name': 'Test Observatory',
        'latitude': 40.7128,
        'longitude': -74.0060,
        'elevation': 100.0,
    }


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Allow database access for all tests.
    This fixture is automatically used for all tests.
    """
    pass