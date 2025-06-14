"""
Basic tests to verify pytest configuration is working.
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User


class BasicTestCase(TestCase):
    """Basic tests to ensure pytest is configured correctly."""

    def test_pytest_is_working(self):
        """Test that pytest is running correctly."""
        assert True

    def test_django_settings(self):
        """Test that Django settings are loaded."""
        from django.conf import settings
        assert settings.DEBUG is not None

    def test_database_connection(self):
        """Test that database connection works."""
        user_count = User.objects.count()
        assert user_count >= 0


@pytest.mark.unit
def test_simple_math():
    """Simple unit test to verify pytest markers work."""
    assert 2 + 2 == 4


@pytest.mark.slow
def test_slow_operation():
    """Test marked as slow for selective running."""
    import time
    time.sleep(0.1)  # Simulate slow operation
    assert True