from django.apps import AppConfig


class StarsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stars_app'
    
    def ready(self):
        # Import signals when the app is ready to ensure they're registered:
        import stars_app.signals
