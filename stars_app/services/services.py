import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from stars_app.models.celestialevent import CelestialEvent
import re
from stars_app.utils import AstronomicalCoordinates


# METEOR SERVICE ---------------------------------------------------- #

class MeteorShowerService:
    def __init__(self):
        self.calendar_url = "https://www.amsmeteors.org/meteor-showers/meteor-shower-calendar/"
        self.coords = AstronomicalCoordinates()

    def fetch_meteor_showers(self):
        """Fetch meteor shower data from American Meteor Society calendar"""
        try:
            # Set up headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            print("Fetching meteor shower calendar...")
            response = requests.get(self.calendar_url, headers=headers)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all shower elements
            shower_elements = soup.find_all('div', class_='shower media')
            print(f"Found {len(shower_elements)} meteor showers")

            showers = []
            for element in shower_elements:
                shower_data = self._process_shower_element(element)
                if shower_data:
                    showers.append(shower_data)

            print(f"Successfully processed {len(showers)} meteor showers")
            return showers

        except Exception as e:
            print(f"Error processing meteor shower data: {str(e)}")
            return []

    def _process_shower_element(self, element):
        """Process a shower element and extract data"""
        try:
            # Get the shower body content
            body = element.find('div', class_='media-body')
            if not body:
                print("No media-body found in shower element")
                return None

            # Get shower name from h3
            name_elem = body.find('h3', class_='media-heading')
            if not name_elem:
                print("No name found in shower element")
                return None

            # Clean up the name
            name = name_elem.text.strip()
            print(f"\nProcessing shower: {name}")

            # Verify the shower exists in our astronomical data
            test_coords = self.coords.get_shower_coordinates(name)
            if test_coords is None:
                print(f"Warning: No astronomical data found for {name}")
                return None

            # Find the activity span
            activity_span = body.find('span', class_='shower_acti')
            if not activity_span:
                print(f"No activity span found for {name}")
                return None

            # Extract activity text
            activity_text = activity_span.get_text(separator=' ', strip=True)

            # Parse dates using different patterns for current and future events
            if 'Currently active' in activity_text:
                dates = re.search(r'Active from\s+(\w+ \d+\w*)\s+to\s+(\w+ \d+\w*,\s*\d{4})', activity_text)
                if dates:
                    year = re.search(r'\d{4}', dates.group(2)).group(0)
                    start_date = f"{dates.group(1)} {year}"
                    end_date = dates.group(2)
            else:
                dates = re.search(r'Next period of activity:\s+(\w+ \d+\w*,\s*\d{4})\s+to\s+(\w+ \d+\w*,\s*\d{4})', activity_text)
                if dates:
                    start_date = dates.group(1)
                    end_date = dates.group(2)

            # Find peak date
            peak_date = None
            for p in body.find_all('p'):
                if 'next peak' in p.text.lower():
                    peak_match = re.search(r'next peak on the (\w+ \d+\w*-\d+,\s*\d{4})', p.text)
                    if peak_match:
                        peak_date = peak_match.group(1).split('-')[0] + peak_match.group(1)[peak_match.group(1).find(','):]
                    break

            # Find ZHR
            zhr = 10  # default value
            for p in body.find_all('p'):
                zhr_match = re.search(r'ZHR:\s*(\d+)', p.text)
                if zhr_match:
                    zhr = int(zhr_match.group(1))
                    break

            if all([start_date, end_date, peak_date]):
                return {
                    'name': name,
                    'start_date': self._parse_date(start_date),
                    'end_date': self._parse_date(end_date),
                    'peak_date': self._parse_date(peak_date),
                    'zhr': zhr,
                    'notes': body.get_text(separator='\n', strip=True)
                }
            else:
                print(f"Missing required dates for {name}")
                return None

        except Exception as e:
            print(f"Error processing shower element: {str(e)}")
            print("Full error details:", e.__class__.__name__, str(e))
            return None

    def _parse_date(self, date_str):
        """Parse date string from text"""
        try:
            # Clean the date string and extract year if present
            date_parts = date_str.strip().replace(',', '').replace('.', '').split()
            if len(date_parts) < 3:  # If year is not in the string
                return None

            month = date_parts[0]
            day = date_parts[1].strip('thstndrd')  # Remove ordinal suffixes
            year = date_parts[2]

            # Reconstruct date string
            clean_date = f"{month} {day} {year}"

            try:
                # Try with full month name
                return datetime.strptime(clean_date, "%B %d %Y").strftime('%Y-%m-%d')
            except ValueError:
                try:
                    # Try with abbreviated month name
                    return datetime.strptime(clean_date, "%b %d %Y").strftime('%Y-%m-%d')
                except ValueError:
                    print(f"Could not parse date: {clean_date}")
                    return None

        except Exception as e:
            print(f"Error parsing date {date_str}: {str(e)}")
            return None

    def _create_meteor_shower_event(self, shower):
        """Create a single meteor shower event at the optimal viewing location"""
        try:
            # Skip if missing required dates
            if not all([shower['start_date'], shower['peak_date'], shower['end_date']]):
                print(f"Skipping {shower['name']} - missing required dates")
                return

            # Parse dates
            start_date = timezone.make_aware(datetime.strptime(shower['start_date'], '%Y-%m-%d'))
            peak_date = timezone.make_aware(datetime.strptime(shower['peak_date'], '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(shower['end_date'], '%Y-%m-%d'))

            # Get optimal viewing location
            locations = self.coords.get_shower_coordinates(shower['name'], peak_date)
            if not locations or not locations[0]:
                print(f"Could not calculate coordinates for {shower['name']}")
                return

            location = locations[0]  # Get the single optimal location

            # Get visibility info for this location
            visibility = self.coords.get_radiant_visibility(
                shower['name'],
                location['latitude'],
                location['longitude'],
                peak_date
            )

            # Create description
            description = (
                f"{shower['name']} Meteor Shower\n\n"
                f"Peak Activity: {shower['peak_date']}\n"
                f"Activity Period: {shower['start_date']} to {shower['end_date']}\n"
                f"Expected Rate: {shower['zhr']} meteors per hour at peak\n\n"
            )

            if visibility:
                description += (
                    f"Viewing Information:\n"
                    f"Best viewing time: {visibility['best_time']}:00 local time\n"
                    f"Maximum radiant altitude: {visibility['max_altitude']:.1f}°\n"
                    f"Visibility score: {visibility['visibility_score']}/100\n\n"
                )

            description += (
                f"Details:\n{shower['notes']}\n\n"
                f"Viewing Tips:\n"
                "- Find a dark location away from city lights\n"
                "- Allow 20-30 minutes for your eyes to adjust to the dark\n"
                "- Look at the entire sky, not just the radiant point\n"
                "- Best viewing is typically between midnight and dawn"
            )

            # Create or update single event
            CelestialEvent.objects.get_or_create(
                name=f"{shower['name']} Meteor Shower",
                start_time=start_date,
                latitude=location['latitude'],
                longitude=location['longitude'],
                defaults={
                    'event_type': 'METEOR',
                    'description': description,
                    'elevation': 0,
                    'end_time': end_date,
                    'viewing_radius': 2000  # Increased radius since we're only showing one location
                }
            )
            print(f"Created/updated event for {shower['name']} Meteor Shower")

        except Exception as e:
            print(f"Error creating event for {shower['name']}: {str(e)}")

    def update_meteor_showers(self):
        """Update meteor shower events in the database"""
        print("Starting meteor shower update...")

        # Fetch and process meteor shower data
        showers = self.fetch_meteor_showers()

        # Create events
        for shower in showers:
            self._create_meteor_shower_event(shower)

        # Report final count
        final_count = CelestialEvent.objects.filter(event_type='METEOR').count()
        print(f"Created {final_count} meteor shower events")


# COMET SERVICE ----------------------------------------------------- #

class CometService:
    def __init__(self):
        self.sbdb_url = "https://ssd-api.jpl.nasa.gov/sbdb.api"

    def fetch_comets(self):
        """Fetch current bright and visible comets from NASA SBDB"""
        try:
            # List of recent and currently visible comets
            # Using the exact designation format from the API
            comet_list = [
                '2023 P1',      # Nishimura
                '2023 A3',      # Tsuchinshan-ATLAS
                '2023 H2',      # Atlas
                '2023 E1',      # NEAT
                '2022 E3',      # ZTF
                '2021 A1'       # Leonard
            ]

            all_comets = []
            for comet_des in comet_list:
                params = {
                    'des': comet_des  # Use designation without C/ prefix
                }

                print(f"Fetching data for comet {comet_des}...")
                print(f"Using URL: {self.sbdb_url}?des={comet_des}")

                response = requests.get(
                    self.sbdb_url,
                    params=params,
                    timeout=10
                )

                print(f"Response status code: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Successfully parsed JSON response for {comet_des}")
                    if data.get('object'):
                        all_comets.append(data)
                        print(f"Added comet data: {data['object'].get('fullname', comet_des)}")
                else:
                    print(f"Error response for {comet_des}: {response.text}")

            print(f"Total comets found: {len(all_comets)}")
            return all_comets

        except Exception as e:
            print(f"Error fetching comet data: {str(e)}")
            return []

    def _calculate_comet_position(self, comet_data):
        """Calculate position from orbital elements"""
        try:
            if not comet_data.get('orbit'):
                print("No orbit data available")
                return None

            orbit = comet_data['orbit']
            elements = orbit.get('elements', [])

            # Extract orbital elements from the array
            orbital_params = {}
            for element in elements:
                orbital_params[element.get('name')] = element.get('value')

            # Calculate coordinates
            dec = float(orbital_params.get('i', 0))    # Use inclination for latitude
            ra = float(orbital_params.get('om', 0))    # Use ascending node for longitude

            # Ensure latitude is within valid range (-90 to 90)
            if dec > 90:
                dec = 180 - dec
            elif dec < -90:
                dec = -180 - dec

            # Convert longitude to -180 to 180 range
            lon = ((ra + 180) % 360) - 180

            position = {
                'latitude': dec,  # Must be between -90 and 90
                'longitude': lon, # Must be between -180 and 180
                'altitude': 0,
                'magnitude': comet_data.get('object', {}).get('magnitude', 'Unknown'),
                'uncertainty': 'Based on orbital elements'
            }

            print(f"Calculated position: {position}")
            return position

        except Exception as e:
            print(f"Error calculating position: {str(e)}")
            return None

    def _create_comet_event(self, comet_data):
        """Create or update a comet event in the database"""
        try:
            current_time = timezone.now()

            # Get comet information
            comet_obj = comet_data.get('object', {})
            fullname = comet_obj.get('fullname', 'Unknown Comet')

            position = self._calculate_comet_position(comet_data)
            if not position:
                print(f"No position data available for {fullname}")
                return

            # Create description
            description = f"Comet {fullname}\n\n"

            # Add orbit class if available
            if comet_obj.get('orbit_class'):
                description += f"Orbit Class: {comet_obj['orbit_class'].get('name', 'Unknown')}\n"

            description += (
                f"\nPosition Information:\n"
                f"Right Ascension: {position['longitude']:.2f}°\n"
                f"Declination: {position['latitude']:.2f}°\n"
                f"Distance: {position['altitude']/1000000:.1f} million km\n"
            )

            # Add orbit information if available
            if comet_data.get('orbit'):
                orbit = comet_data['orbit']
                description += (
                    f"\nOrbit Information:\n"
                    f"First Observed: {orbit.get('first_obs', 'Unknown')}\n"
                    f"Last Observed: {orbit.get('last_obs', 'Unknown')}\n"
                )

            description += (
                f"\nViewing Tips:\n"
                "- Best viewed from dark sky locations\n"
                "- Use binoculars or a small telescope\n"
                "- Check local astronomy resources for precise viewing times\n"
                "- Position updates weekly"
            )

            # Create or update the event
            CelestialEvent.objects.get_or_create(
                name=f"Comet {fullname}",
                start_time=current_time,
                latitude=position['latitude'],
                longitude=position['longitude'],
                defaults={
                    'event_type': 'COMET',
                    'description': description,
                    'elevation': position['altitude'],
                    'end_time': current_time + timedelta(days=7),
                    'viewing_radius': 1000
                }
            )
            print(f"Created/updated event for {fullname}")

        except Exception as e:
            print(f"Error creating comet event: {str(e)}")
            print(f"Comet data: {comet_data}")

    def update_comets(self):
        """Update comet events in the database"""
        print("Starting comet update...")

        # Fetch current comet data
        comets = self.fetch_comets()

        if not comets:
            print("No comets found")
            return

        # Process each comet
        for comet in comets:
            self._create_comet_event(comet)

        # Report final count
        final_count = CelestialEvent.objects.filter(event_type='COMET').count()
        print(f"Created {final_count} comet events")

