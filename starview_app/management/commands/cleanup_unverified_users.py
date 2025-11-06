"""
Management command to delete users who haven't verified their email within a specified timeframe.

Usage:
    python manage.py cleanup_unverified_users --days=7

Purpose:
    Prevents email squatting and database bloat from unverified user accounts.
    Should be run periodically via cron job (daily or weekly).

Arguments:
    --days: Number of days after registration to delete unverified users (default: 7)
    --dry-run: Preview what would be deleted without actually deleting
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = 'Delete users who have not verified their email after X days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete unverified users older than this many days (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=days)

        # Find all unverified email addresses for users registered before cutoff date
        unverified_emails = EmailAddress.objects.filter(
            verified=False,
            user__date_joined__lt=cutoff_date
        ).select_related('user')

        count = unverified_emails.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No unverified users found to delete.'))
            return

        # Display what will be deleted
        self.stdout.write(f'\nFound {count} unverified user(s) older than {days} days:')
        self.stdout.write(f'Cutoff date: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}\n')

        for email_address in unverified_emails:
            user = email_address.user
            days_old = (timezone.now() - user.date_joined).days
            self.stdout.write(
                f'  - {user.username} ({user.email}) - registered {days_old} days ago'
            )

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n[DRY RUN] Would have deleted {count} users'))
            return

        # Delete unverified users
        self.stdout.write('\nDeleting unverified users...')
        deleted_count = 0

        for email_address in unverified_emails:
            user = email_address.user
            username = user.username
            email = user.email

            try:
                user.delete()  # This cascades and deletes EmailAddress too
                deleted_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted: {username} ({email})'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed to delete {username}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully deleted {deleted_count} unverified user(s)'))
