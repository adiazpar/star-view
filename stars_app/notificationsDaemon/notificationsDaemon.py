import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.utils.timezone import localtime
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
import django

sys.path.append('/environment/Group8-fall2024')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from stars_app.models import FavoriteLocation, CelestialEvent

# temporal filter for upcoming events 
TIME_FRAME = timedelta(hours=24)
LAT_LON_TOLERANCE = 0.01  

# gmail credentials 
GMAIL_USER = 'eventhorizonnotifications@gmail.com'
GMAIL_APP_PASSWORD = 'xqep zusl cwdl xxot'

def get_favorites_and_events():
	now = make_aware(datetime.now())
	future = now + TIME_FRAME
	users = User.objects.all()
	for user in users:
		print(f"User: {user.username} ({user.email})")
		print("All events in the database:")
		all_events = CelestialEvent.objects.all()
		for event in all_events:
			print(f"  - {event.name}: ({event.latitude}, {event.longitude}) from {event.start_time} to {event.end_time}")
		favorite_locations = FavoriteLocation.objects.filter(user=user)
		if favorite_locations.exists():
			print("  Favorite Locations:")
			for fav in favorite_locations:
				print(f"    - {fav.location.name} ({fav.location.latitude}, {fav.location.longitude})")
			all_matching_events = []
			upcoming_matching_events = []
			all_events = CelestialEvent.objects.all()
			for event in all_events:
				for fav in favorite_locations:
					if (
						abs(event.latitude - fav.location.latitude) <= LAT_LON_TOLERANCE and
						abs(event.longitude - fav.location.longitude) <= LAT_LON_TOLERANCE
					):
						all_matching_events.append(event)
						if now <= event.start_time <= future:
							upcoming_matching_events.append(event)
						break
			if upcoming_matching_events:
				send_event_notification(user.username, user.email, upcoming_matching_events)
				print("  Upcoming Events in the next 24 hours:")
				for event in upcoming_matching_events:
					print(f"    - {event.name} at ({event.latitude}, {event.longitude}) from {event.start_time} to {event.end_time}")
			else:
				print("  No upcoming events in the next 24 hours.")

			if all_matching_events:
				print("  All Events at Favorite Locations:")
				for event in all_matching_events:
					print(f"    - {event.name} at ({event.latitude}, {event.longitude}) from {event.start_time} to {event.end_time}")
			else:
				print("  No events found at favorite locations.")
		else:
			print("  No favorite locations.")

def send_event_notification(user, recipient_email, upcoming_matching_events):
	recipient_email = "jason@fastmail.org"
	try:
		subject = "Upcoming Celestial Events at Your Favorite Locations"
		
		if not upcoming_matching_events:
			body = "There are no upcoming celestial events at your favorite locations in the next 24 hours."
		else:
			body = f"Hi {user}!\n Here are the upcoming celestial events at your favorite locations happening in the next 24 hours!:\n\n"
			for event in upcoming_matching_events:
				body += (
					f"- {event.name} ({event.event_type})\n"
					f"  Location: ({event.latitude}, {event.longitude})\n"
					f"  Start: {localtime(event.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n"
					f"  End: {localtime(event.end_time).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
				)

		msg = MIMEMultipart()
		msg['From'] = GMAIL_USER
		msg['To'] = recipient_email
		msg['Subject'] = subject
		msg.attach(MIMEText(body, 'plain'))
		with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
			server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
			server.send_message(msg)
		print(f"Email successfully sent to {recipient_email}")
	except Exception as e:
		print(f"Failed to send email: {e}")

if __name__ == "__main__":
	get_favorites_and_events()

