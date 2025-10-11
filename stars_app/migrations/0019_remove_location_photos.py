# Manual migration to remove LocationPhoto model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stars_app', '0018_delete_celestialevent'),
    ]

    operations = [
        # Drop LocationPhoto table directly
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS stars_app_locationphoto;',
            reverse_sql='',  # Not reversible
        ),
    ]
