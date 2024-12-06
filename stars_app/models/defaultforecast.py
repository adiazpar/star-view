from .forecast import Forecast


# Default Forecast Model for Initial Migration ---------------------- #
def defaultforecast():
    tmp = Forecast.objects.create()
    return tmp.id
