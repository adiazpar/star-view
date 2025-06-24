import os
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from stars_app.models import UserProfile, LocationPhoto, ReviewPhoto, ViewingLocation, LocationReview
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Clean up orphaned media files that are no longer referenced by database records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting files',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No files will be deleted')
            )
        
        self.stdout.write('Starting orphaned media cleanup...')
        
        # Clean up each media type
        profile_pics_cleaned = self.cleanup_profile_pictures()
        location_photos_cleaned = self.cleanup_location_photos()
        review_photos_cleaned = self.cleanup_review_photos()
        
        # Summary
        total_cleaned = profile_pics_cleaned + location_photos_cleaned + review_photos_cleaned
        
        if self.dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN COMPLETE: Found {total_cleaned} orphaned files that would be deleted'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'CLEANUP COMPLETE: Deleted {total_cleaned} orphaned files'
                )
            )

    def cleanup_profile_pictures(self):
        """Clean up orphaned profile pictures"""
        self.stdout.write('Checking profile pictures...')
        
        profile_pics_dir = os.path.join(settings.MEDIA_ROOT, 'profile_pics')
        if not os.path.exists(profile_pics_dir):
            return 0
        
        # Get all files in profile_pics directory
        all_files = []
        for root, dirs, files in os.walk(profile_pics_dir):
            for file in files:
                all_files.append(os.path.join(root, file))
        
        # Get all profile picture paths from database
        valid_paths = set()
        for profile in UserProfile.objects.exclude(profile_picture='').exclude(profile_picture__isnull=True):
            if profile.profile_picture:
                valid_paths.add(profile.profile_picture.path)
        
        # Find orphaned files
        orphaned_files = []
        for file_path in all_files:
            if file_path not in valid_paths:
                orphaned_files.append(file_path)
        
        # Delete orphaned files
        deleted_count = 0
        for file_path in orphaned_files:
            if self.verbose:
                self.stdout.write(f'  Orphaned profile pic: {file_path}')
            
            if not self.dry_run:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except OSError as e:
                    self.stdout.write(
                        self.style.ERROR(f'  Error deleting {file_path}: {e}')
                    )
            else:
                deleted_count += 1
        
        self.stdout.write(f'  Profile pictures: {deleted_count} files processed')
        return deleted_count

    def cleanup_location_photos(self):
        """Clean up orphaned location photos"""
        self.stdout.write('Checking location photos...')
        
        location_photos_dir = os.path.join(settings.MEDIA_ROOT, 'location_photos')
        if not os.path.exists(location_photos_dir):
            return 0
        
        # Get all files in location_photos directory
        all_files = []
        for root, dirs, files in os.walk(location_photos_dir):
            for file in files:
                all_files.append(os.path.join(root, file))
        
        # Get all valid location photo paths from database
        valid_paths = set()
        for photo in LocationPhoto.objects.all():
            if photo.image:
                valid_paths.add(photo.image.path)
            if photo.thumbnail:
                valid_paths.add(photo.thumbnail.path)
        
        # Find orphaned files
        orphaned_files = []
        orphaned_dirs = set()
        
        for file_path in all_files:
            if file_path not in valid_paths:
                orphaned_files.append(file_path)
                # Track directories that might become empty
                orphaned_dirs.add(os.path.dirname(file_path))
        
        # Delete orphaned files
        deleted_count = 0
        for file_path in orphaned_files:
            if self.verbose:
                self.stdout.write(f'  Orphaned location photo: {file_path}')
            
            if not self.dry_run:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except OSError as e:
                    self.stdout.write(
                        self.style.ERROR(f'  Error deleting {file_path}: {e}')
                    )
            else:
                deleted_count += 1
        
        # Clean up empty directories
        if not self.dry_run:
            for dir_path in orphaned_dirs:
                self._cleanup_empty_directory(dir_path)
        
        self.stdout.write(f'  Location photos: {deleted_count} files processed')
        return deleted_count

    def cleanup_review_photos(self):
        """Clean up orphaned review photos"""
        self.stdout.write('Checking review photos...')
        
        review_photos_dir = os.path.join(settings.MEDIA_ROOT, 'review_photos')
        if not os.path.exists(review_photos_dir):
            return 0
        
        # Get all files in review_photos directory
        all_files = []
        for root, dirs, files in os.walk(review_photos_dir):
            for file in files:
                all_files.append(os.path.join(root, file))
        
        # Get all valid review photo paths from database
        valid_paths = set()
        for photo in ReviewPhoto.objects.all():
            if photo.image:
                valid_paths.add(photo.image.path)
            if photo.thumbnail:
                valid_paths.add(photo.thumbnail.path)
        
        # Find orphaned files and directories
        orphaned_files = []
        orphaned_dirs = set()
        
        for file_path in all_files:
            if file_path not in valid_paths:
                orphaned_files.append(file_path)
                # Track directories that might become empty
                orphaned_dirs.add(os.path.dirname(file_path))
        
        # Also check for directories of deleted reviews/locations
        self._find_orphaned_review_directories(review_photos_dir, orphaned_dirs)
        
        # Delete orphaned files
        deleted_count = 0
        for file_path in orphaned_files:
            if self.verbose:
                self.stdout.write(f'  Orphaned review photo: {file_path}')
            
            if not self.dry_run:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except OSError as e:
                    self.stdout.write(
                        self.style.ERROR(f'  Error deleting {file_path}: {e}')
                    )
            else:
                deleted_count += 1
        
        # Clean up empty directories
        if not self.dry_run:
            for dir_path in orphaned_dirs:
                self._cleanup_empty_directory(dir_path)
        
        self.stdout.write(f'  Review photos: {deleted_count} files processed')
        return deleted_count

    def _find_orphaned_review_directories(self, review_photos_dir, orphaned_dirs):
        """Find directories for deleted locations or reviews"""
        if not os.path.exists(review_photos_dir):
            return
        
        # Get valid location IDs
        valid_location_ids = set(str(loc_id) for loc_id in ViewingLocation.objects.values_list('id', flat=True))
        
        # Get valid review IDs per location
        valid_review_ids = {}
        for review in LocationReview.objects.all():
            location_id = str(review.location_id)
            if location_id not in valid_review_ids:
                valid_review_ids[location_id] = set()
            valid_review_ids[location_id].add(str(review.id))
        
        # Check each location directory
        for item in os.listdir(review_photos_dir):
            location_dir = os.path.join(review_photos_dir, item)
            if os.path.isdir(location_dir):
                location_id = item
                
                # If location doesn't exist, mark entire directory for cleanup
                if location_id not in valid_location_ids:
                    orphaned_dirs.add(location_dir)
                    if self.verbose:
                        self.stdout.write(f'  Orphaned location directory: {location_dir}')
                else:
                    # Check review directories within this location
                    for review_item in os.listdir(location_dir):
                        review_dir = os.path.join(location_dir, review_item)
                        if os.path.isdir(review_dir) and review_item != 'thumbnails':
                            review_id = review_item
                            
                            # If review doesn't exist, mark for cleanup
                            if (location_id not in valid_review_ids or 
                                review_id not in valid_review_ids[location_id]):
                                orphaned_dirs.add(review_dir)
                                if self.verbose:
                                    self.stdout.write(f'  Orphaned review directory: {review_dir}')

    def _cleanup_empty_directory(self, dir_path):
        """Recursively clean up empty directories"""
        try:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                # Try to remove if empty
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    if self.verbose:
                        self.stdout.write(f'  Removed empty directory: {dir_path}')
                    
                    # Try to clean up parent directory too
                    parent_dir = os.path.dirname(dir_path)
                    if parent_dir != settings.MEDIA_ROOT:
                        self._cleanup_empty_directory(parent_dir)
        except OSError:
            # Directory not empty or other error, ignore
            pass