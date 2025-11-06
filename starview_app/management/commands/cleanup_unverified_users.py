"""
Management command to delete users who haven't verified their email within a specified timeframe
and clean up expired/orphaned email confirmations.

Usage:
    python manage.py cleanup_unverified_users --days=7

Purpose:
    1. Prevents email squatting and database bloat from unverified user accounts
    2. Cleans up expired/orphaned email confirmation tokens
    Should be run periodically via cron job (daily or weekly).

What gets cleaned:
    - Unverified users older than X days (default: 7)
    - Expired email confirmations (older than ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS)
    - Orphaned email confirmations (user deleted but confirmation remains)

Arguments:
    --days: Number of days after registration to delete unverified users (default: 7)
    --dry-run: Preview what would be deleted without actually deleting
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress, EmailConfirmation
from django.conf import settings


class Command(BaseCommand):
    help = 'Delete unverified users and clean up expired/orphaned email confirmations'

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

        # ========================================
        # Part 1: Delete unverified users
        # ========================================

        # Find all unverified email addresses for users registered before cutoff date
        unverified_emails = EmailAddress.objects.filter(
            verified=False,
            user__date_joined__lt=cutoff_date
        ).select_related('user')

        user_count = unverified_emails.count()

        if user_count > 0:
            # Display what will be deleted
            self.stdout.write(f'\nFound {user_count} unverified user(s) older than {days} days:')
            self.stdout.write(f'Cutoff date: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}\n')

            for email_address in unverified_emails:
                user = email_address.user
                days_old = (timezone.now() - user.date_joined).days
                self.stdout.write(
                    f'  - {user.username} ({user.email}) - registered {days_old} days ago'
                )

            if not dry_run:
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
        else:
            self.stdout.write(self.style.SUCCESS('No unverified users found to delete.'))

        # ========================================
        # Part 2: Clean up expired/orphaned email confirmations
        # ========================================

        self.stdout.write('\n' + '='*60)
        self.stdout.write('Cleaning up email confirmations...')
        self.stdout.write('='*60)

        # Get expiry days from settings (default: 3 days)
        expiry_days = getattr(settings, 'ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS', 3)
        confirmation_cutoff = timezone.now() - timedelta(days=expiry_days)

        # Find expired confirmations
        expired_confirmations = EmailConfirmation.objects.filter(
            sent__lt=confirmation_cutoff
        )

        # Find orphaned confirmations (email address no longer exists)
        orphaned_confirmations = EmailConfirmation.objects.filter(
            email_address__isnull=True
        )

        # Combine both querysets
        total_confirmations = expired_confirmations | orphaned_confirmations
        confirmation_count = total_confirmations.distinct().count()

        if confirmation_count > 0:
            self.stdout.write(f'\nFound {confirmation_count} confirmation(s) to clean up:')

            expired_count = expired_confirmations.count()
            orphaned_count = orphaned_confirmations.count()

            if expired_count > 0:
                self.stdout.write(f'  - {expired_count} expired confirmation(s) (>{expiry_days} days old)')
            if orphaned_count > 0:
                self.stdout.write(f'  - {orphaned_count} orphaned confirmation(s) (email address deleted)')

            if dry_run:
                self.stdout.write(self.style.WARNING(f'\n[DRY RUN] Would have deleted {confirmation_count} confirmation(s)'))
            else:
                # Delete confirmations
                deleted_count, _ = total_confirmations.delete()
                self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully deleted {deleted_count} email confirmation(s)'))
        else:
            self.stdout.write(self.style.SUCCESS('No expired or orphaned confirmations found.'))

        # ========================================
        # Summary
        # ========================================

        if dry_run:
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.WARNING('[DRY RUN] No changes made to database'))
            self.stdout.write('='*60)
