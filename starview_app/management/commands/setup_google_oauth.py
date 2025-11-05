"""
Management command to set up Google OAuth provider.

This command creates or updates the Google SocialApp configuration
using credentials from environment variables.

Usage:
    python manage.py setup_google_oauth
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Set up Google OAuth provider using credentials from .env file'

    def handle(self, *args, **options):
        # Get credentials from environment
        client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR(
                'ERROR: GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set in .env file'
            ))
            return

        # Get or create the Site (SITE_ID = 1)
        try:
            site = Site.objects.get(id=1)
            self.stdout.write(f'Using site: {site.domain} (ID: {site.id})')
        except Site.DoesNotExist:
            site = Site.objects.create(id=1, domain='127.0.0.1:8000', name='Starview Local')
            self.stdout.write(self.style.SUCCESS(f'Created site: {site.domain}'))

        # Create or update Google SocialApp
        social_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': client_id,
                'secret': client_secret,
            }
        )

        if not created:
            # Update existing app
            social_app.client_id = client_id
            social_app.secret = client_secret
            social_app.save()
            self.stdout.write(self.style.SUCCESS('✅ Updated existing Google OAuth app'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Created new Google OAuth app'))

        # Associate with site
        if site not in social_app.sites.all():
            social_app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(f'✅ Associated Google app with site: {site.domain}'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Google OAuth setup complete!'))
        self.stdout.write('Google Login URL: http://127.0.0.1:8000/accounts/google/login/')
