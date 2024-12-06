from django.db import models

# Forecast Model --------------------------------------------------- #
class Forecast(models.Model):
	createTime = models.DateTimeField(auto_now=True) #when model is created or updated get new time
	forecast = models.JSONField(default=list, null=True)