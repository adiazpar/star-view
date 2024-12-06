from django.contrib import admin

from stars_app.models.userprofile import UserProfile
from stars_app.models.celestialevent import CelestialEvent
from stars_app.models.favoritelocation import FavoriteLocation
from stars_app.models.viewinglocation import ViewingLocation
from stars_app.models.forecast import Forecast

# Register your models here.
admin.site.register(ViewingLocation)
admin.site.register(CelestialEvent)
admin.site.register(UserProfile)
admin.site.register(FavoriteLocation)
admin.site.register(Forecast)
