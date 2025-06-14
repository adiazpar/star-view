from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from stars_app.models.userprofile import UserProfile


class Command(BaseCommand):
    help = 'Update reputation scores for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Update reputation for specific username'
        )

    def handle(self, *args, **options):
        username = options.get('user')
        
        if username:
            try:
                user = User.objects.get(username=username)
                users = [user]
            except User.DoesNotExist:
                self.stderr.write(f'User {username} not found')
                return
        else:
            users = User.objects.all()
        
        updated_count = 0
        
        for user in users:
            try:
                profile, created = UserProfile.objects.get_or_create(user=user)
                old_score = profile.reputation_score
                new_score = profile.calculate_reputation()
                profile.save()
                
                if old_score != new_score:
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated {user.username}: {old_score} -> {new_score} '
                            f'(Trusted: {profile.is_trusted_contributor})'
                        )
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating {user.username}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} user reputations')
        )