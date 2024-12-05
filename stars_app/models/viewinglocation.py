from django.db import models
from django.contrib.auth.models import User
from datetime import timezone
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .forecast import Forecast
from .defaultforecast import defaultforecast

# Viewing Location Model -------------------------------------------- #
class ViewingLocation(models.Model):
	name = models.CharField(max_length=200)
	latitude = models.FloatField()
	longitude = models.FloatField()
	elevation = models.FloatField(help_text="Elevation in meters")

	forecast = models.ForeignKey(Forecast, on_delete=models.CASCADE, default=defaultforecast) 
	cloudCoverPercentage = models.FloatField(null=True)

	light_pollution_value = models.FloatField(null=True, blank=True, help_text="Calculated light pollution value from tiles")
	quality_score = models.FloatField(null=True, blank=True)

	added_by = models.ForeignKey(User, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	def getForecast(self, hours=10): #gets the forcasted cloud cover with 10 or the maximum the api will supply XXX will only work for the US
		base_url = "https://graphical.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php"
		start_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
		end_time = (datetime.now(timezone.utc) + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")

		params = {
		"lat": self.latitude,
		"lon": self.longitude,
		"product": "time-series",
		"begin": start_time,
		"end": end_time,
		"sky": "sky"
		}
		try:
			response = requests.get(base_url, params=params)
			response.raise_for_status()  # Raise an error for bad status codes
			#print("API Response XML:")
			#print(response.text)
			root = ET.fromstring(response.content)
			cloud_cover = []
			for value in root.findall(".//parameters/cloud-amount/value"):
				if value.text is not None:
					cloud_cover.append(int(value.text))
			return cloud_cover[:hours]
		except Exception as e:
			print(f"An error occurred: {e}")
			return []
	def updateForecast(self):
		if not self.forecast.forecast:
			forecast_data = self.getForecast()
			if not forecast_data:
				self.cloudCoverPercentage = -1
				self.forecast.forecast = []  
				self.forecast.save()
				return
			self.forecast.forecast = forecast_data
			self.forecast.save()
		if self.cloudCoverPercentage == -1: #if it is outside the US / NDF grid
			return
		currentTime = datetime.now().replace(tzinfo=ZoneInfo("America/Denver"))
		beginTime = self.forecast.createTime
		dateDelta = currentTime - beginTime
		days, seconds = dateDelta.days, dateDelta.seconds
		hours = int(days * 24 + seconds / 3600)
		if hours >= len(self.forecast.forecast):
			forecast_data = self.getForecast()
			if not forecast_data:
				self.cloudCoverPercentage = -1
				self.forecast.forecast = []  
				self.forecast.save()
				return
			self.forecast.forecast = forecast_data
			self.forecast.save()
		if hours < len(self.forecast.forecast):
			self.cloudCoverPercentage = self.forecast.forecast[hours]
		else:
			self.cloudCoverPercentage = -1  
		self.forecast.save()

	def __str__(self):
		return f"{self.name} ({self.latitude}, {self.longitude})"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.updateForecast()