from django.utils import timezone
from .forecast import Forecast


# Default Forecast Model for Initial Migration ---------------------- #
def defaultforecast():
    """Creates and returns a default forecast instance ID.
    This function is used as the default value for ViewingLocation's forecast field."""
    return Forecast.objects.create(
        forecast=[],  # Empty list for initial forecast
        createTime=timezone.now()
    ).pk

get_default_forecast = defaultforecast
