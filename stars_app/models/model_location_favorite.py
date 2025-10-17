from django.db import models
from django.contrib.auth.models import User

from .model_location import Location


# Favorite Location Model ------------------------------------------- #
class FavoriteLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_locations')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='favorited_by')
    nickname = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # This makes sure a user can't favorite the same location multiple times:
        unique_together = ['user', 'location']

    def get_display_name(self, max_length=25):
        name = self.nickname if self.nickname else self.location.name
        if len(name) > max_length:
            return f"{name[:max_length]}..."
        return name

    def get_original_name(self, max_length=25):
        name = self.location.name
        if len(name) > max_length:
            return f"{name[:max_length]}..."
        return name

    def __str__(self):
        display_name = self.nickname if self.nickname else self.location.name
        return f'{self.user.username} - {display_name}'
