# Add missing timestamp fields to CelestialEvent and other models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stars_app', '0002_add_missing_fields'),
    ]

    operations = [
        # Add timestamp fields to CelestialEvent
        migrations.AddField(
            model_name='celestialevent',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='celestialevent',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Add timestamp fields to UserProfile (if missing)
        migrations.AddField(
            model_name='userprofile',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]