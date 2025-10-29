# ----------------------------------------------------------------------------------------------------- #
# This signals.py file handles Django signal receivers for the stars_app:                               #
#                                                                                                       #
# Model Creation Signals (post_save):                                                                   #
# - User creation → Automatically creates associated UserProfile                                        #
#                                                                                                       #
# File Cleanup Signals (pre_delete, post_delete):                                                       #
# 1. UserProfile deletion → Removes profile pictures                                                    #
# 2. ReviewPhoto deletion → Removes review images and thumbnails                                        #
# 3. Review deletion → Coordinates cleanup of all associated photos                                     #
# 4. Location deletion → Coordinates cleanup of all reviews and photos via CASCADE                      #
#                                                                                                       #
# Cleanup happens in phases:                                                                            #
# - pre_delete: Delete files before database deletion (while paths are still accessible)                #
# - post_delete: Clean up empty directories after CASCADE deletions complete                            #
#                                                                                                       #
# Signal Registration:                                                                                  #
# These signals are automatically registered when this module is imported via stars_app/apps.py         #
# in the ready() method.                                                                                #
#                                                                                                       #
# Safety Features:                                                                                      #
# - Files are only deleted if they're within MEDIA_ROOT (security check)                                #
# - Empty directories are cleaned up automatically                                                      #
# - Handles CASCADE deletions properly (Location → Reviews → Photos)                                    #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
import os
from django.db.models.signals import pre_delete, post_delete, post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User
from pathlib import Path

# Import models:
from starview_app.models import UserProfile
from starview_app.models import ReviewPhoto
from starview_app.models import Review
from starview_app.models import Location



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                           SIGNAL METHODS                                              #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Safely delete a file from the filesystem with error handling.                 #
#                                                                               #
# Args:       file_path (str): Path to the file to delete                       #
# Returns:    bool: True if deleted successfully, False otherwise               #
# ----------------------------------------------------------------------------- #
def safe_delete_file(file_path):
    if not file_path:
        return False

    try:
        # Convert to Path object for better handling:
        path = Path(file_path)

        # Check if file exists and is within media directory (security check):
        if path.exists() and str(path).startswith(str(settings.MEDIA_ROOT)):
            # File gets deleted:
            path.unlink()
            return True
        elif not path.exists():
            # File already deleted or doesn't exist:
            return True
        else:
            # File outside of media directory, so it doesn't get deleted:
            return False

    except Exception:
        # There was an error deleting the file:
        return False


# ----------------------------------------------------------------------------- #
# Safely delete an empty directory and its empty parent directories.            #
#                                                                               #
# Args:   dir_path (str): Path to the directory to delete                       #
# ----------------------------------------------------------------------------- #
def safe_delete_directory(dir_path):
    if not dir_path:
        return

    try:
        path = Path(dir_path)

        # Only delete if it's within media directory and is empty:
        if (path.exists() and
                str(path).startswith(str(settings.MEDIA_ROOT)) and
                path.is_dir() and
                not any(path.iterdir())):

            # Delete empty directory:
            path.rmdir()

            # Try to delete parent directory if it's also empty:
            parent = path.parent
            if (parent != Path(settings.MEDIA_ROOT) and
                    parent.exists() and
                    parent.is_dir() and
                    not any(parent.iterdir())):
                safe_delete_directory(str(parent))

    except Exception:
        # There was an error deleting the directory:
        return



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                               SIGNALS                                                 #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# Deletes user profile picture when user profile is deleted:
@receiver(pre_delete, sender=UserProfile)
def delete_user_profile_picture(instance, **kwargs):
    if instance.profile_picture:
        file_path = instance.profile_picture.path
        safe_delete_file(file_path)

        # Try to clean up empty directory:
        dir_path = os.path.dirname(file_path)
        safe_delete_directory(dir_path)


# Delete review photo and thumbnail files when ReviewPhoto is deleted:
@receiver(pre_delete, sender=ReviewPhoto)
def delete_review_photo_files(instance, **kwargs):
    files_to_delete = []

    # Add main image:
    if instance.image:
        files_to_delete.append(instance.image.path)

    # Add thumbnail:
    if instance.thumbnail:
        files_to_delete.append(instance.thumbnail.path)

    # Delete all files:
    for file_path in files_to_delete:
        safe_delete_file(file_path)

    # Clean up directories if they're empty:
    if instance.image:
        # Get the review-specific directory:
        review_dir = os.path.dirname(instance.image.path)
        safe_delete_directory(os.path.join(review_dir, 'thumbnails'))
        safe_delete_directory(review_dir)

        # Try to clean up location directory if empty:
        location_dir = os.path.dirname(review_dir)
        safe_delete_directory(location_dir)


# Clean up the entire location directory structure after all cascade deletions are complete:
@receiver(post_delete, sender=Location)
def cleanup_location_directory_structure(instance, **kwargs):
    try:
        # Try to clean up the main review photos directory:
        review_photos_dir = os.path.join(settings.MEDIA_ROOT, 'review_photos', str(instance.id))
        safe_delete_directory(review_photos_dir)

    except Exception:
        # There was an error cleaning up directory structure for location:
        return


# Clean up the review directory structure after all cascade deletions are complete:
@receiver(post_delete, sender=Review)
def cleanup_review_directory_structure(instance, **kwargs):
    try:
        # Try to clean up the main review directory:
        review_dir = os.path.join(
            settings.MEDIA_ROOT,
            'review_photos',
            str(instance.location.id),
            str(instance.id)
        )
        safe_delete_directory(review_dir)

    except Exception:
        # There was an error cleaning up directory structure for review:
        return


# Automatically create UserProfile when User is created:
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance)  # Create profile for existing users if missing
