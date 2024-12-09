from datetime import datetime, timedelta
import requests
from django_project import settings


def test_firms_api_correct_format():
    """
    Test the FIRMS API using the correct format from the documentation.
    Uses simple number of days instead of date ranges.
    """
    api_key = settings.NASA_FIRMS_KEY
    base_url = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    # Use a valid bounding box
    west, south = -98.6795, 39.7283
    east, north = -98.4795, 39.9283
    area = f"{west},{south},{east},{north}"

    # Test different day counts
    test_cases = [
        {
            'name': "1 day of data",
            'days': "1",
            'description': "Testing single day retrieval"
        },
        {
            'name': "5 days of data",
            'days': "5",
            'description': "Testing 5-day retrieval"
        },
        {
            'name': "10 days of data",
            'days': "10",
            'description': "Testing maximum day retrieval"
        }
    ]

    print("\nTesting FIRMS API with correct format:")
    print("=" * 50)

    for case in test_cases:
        print(f"\nTest Case: {case['name']}")
        print(f"Description: {case['description']}")

        # Construct URL using just the number of days
        url = f"{base_url}/{api_key}/VIIRS_SNPP_NRT/{area}/{case['days']}"

        print(f"Testing URL: {url}")

        try:
            response = requests.get(url)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:200]}")

            # If we get data back, show a sample
            if response.status_code == 200 and response.text:
                print("\nFirst few lines of data:")
                lines = response.text.split('\n')[:3]
                for line in lines:
                    print(line)

        except Exception as e:
            print(f"Error: {str(e)}")

        print("-" * 50)

    return True