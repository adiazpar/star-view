# Generated migration to add missing fields from base models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stars_app', '0001_initial'),
    ]

    operations = [
        # Add updated_at field to ViewingLocation
        migrations.AddField(
            model_name='viewinglocation',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Add rating fields to ViewingLocation
        migrations.AddField(
            model_name='viewinglocation',
            name='rating_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='viewinglocation',
            name='average_rating',
            field=models.DecimalField(
                decimal_places=2,
                default=0.00,
                help_text="Average rating (0.00-5.00)",
                max_digits=3,
            ),
        ),
    ]