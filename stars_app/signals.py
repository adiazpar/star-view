import os
import logging
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from django.conf import settings
from pathlib import Path

# Import models
from .models.userprofile import UserProfile
from .models.reviewphoto import ReviewPhoto
from .models.locationreview import LocationReview
from .models.viewinglocation import ViewingLocation

logger = logging.getLogger(__name__)


def safe_delete_file(file_path):
    """
    Safely delete a file from the filesystem with error handling.

    Args:
        file_path (str): Path to the file to delete

    Returns:
        bool: True if deleted successfully, False otherwise
    """
    if not file_path:
        return False

    try:
        # Convert to Path object for better handling
        path = Path(file_path)

        # Check if file exists and is within media directory (security check)
        if path.exists() and str(path).startswith(str(settings.MEDIA_ROOT)):
            path.unlink()
            logger.info(f"Deleted file: {file_path}")
            return True
        elif not path.exists():
            logger.debug(f"File already deleted or doesn't exist: {file_path}")
            return True
        else:
            logger.warning(f"File outside media directory, not deleting: {file_path}")
            return False

    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False


def safe_delete_directory(dir_path):
    """
    Safely delete an empty directory and its empty parent directories.

    Args:
        dir_path (str): Path to the directory to delete
    """
    if not dir_path:
        return

    try:
        path = Path(dir_path)

        # Only delete if it's within media directory and is empty
        if (path.exists() and
                str(path).startswith(str(settings.MEDIA_ROOT)) and
                path.is_dir() and
                not any(path.iterdir())):

            path.rmdir()
            logger.info(f"Deleted empty directory: {dir_path}")

            # Try to delete parent directory if it's also empty
            parent = path.parent
            if (parent != Path(settings.MEDIA_ROOT) and
                    parent.exists() and
                    parent.is_dir() and
                    not any(parent.iterdir())):
                safe_delete_directory(str(parent))

    except Exception as e:
        logger.error(f"Error deleting directory {dir_path}: {str(e)}")


@receiver(pre_delete, sender=UserProfile)
def delete_user_profile_picture(sender, instance, **kwargs):
    """
    Delete user profile picture when UserProfile is deleted.
    """
    if instance.profile_picture:
        file_path = instance.profile_picture.path
        safe_delete_file(file_path)

        # Try to clean up empty directory
        dir_path = os.path.dirname(file_path)
        safe_delete_directory(dir_path)


@receiver(pre_delete, sender=ReviewPhoto)
def delete_review_photo_files(sender, instance, **kwargs):
    """
    Delete review photo and thumbnail files when ReviewPhoto is deleted.
    """
    files_to_delete = []

    # Add main image
    if instance.image:
        files_to_delete.append(instance.image.path)

    # Add thumbnail
    if instance.thumbnail:
        files_to_delete.append(instance.thumbnail.path)

    # Delete all files
    for file_path in files_to_delete:
        safe_delete_file(file_path)

    # Clean up directories if they're empty
    if instance.image:
        # Get the review-specific directory
        review_dir = os.path.dirname(instance.image.path)
        safe_delete_directory(os.path.join(review_dir, 'thumbnails'))  # Delete thumbnails dir first
        safe_delete_directory(review_dir)  # Then review dir

        # Try to clean up location directory if empty
        location_dir = os.path.dirname(review_dir)
        safe_delete_directory(location_dir)


@receiver(pre_delete, sender=LocationReview)
def delete_review_media_files(sender, instance, **kwargs):
    """
    Delete all media files associated with a review when the review is deleted.
    This handles the cascade deletion of ReviewPhotos.
    """
    # Get all photos for this review before they're deleted by cascade
    review_photos = instance.photos.all()

    for photo in review_photos:
        # The ReviewPhoto pre_delete signal will handle individual file deletion
        # We just need to ensure the directory structure is cleaned up
        if photo.image:
            # Directory cleanup will be handled by individual photo deletion signals
            pass


@receiver(pre_delete, sender=ViewingLocation)
def delete_location_media_files(sender, instance, **kwargs):
    """
    Delete all media files associated with a location when the location is deleted.
    This handles the cascade deletion of ReviewPhotos.
    """
    # Get all reviews and their photos before they're deleted by cascade
    reviews = instance.reviews.all()

    # Store directory paths for cleanup
    directories_to_clean = set()

    # Process review photos
    for review in reviews:
        for photo in review.photos.all():
            if photo.image:
                review_dir = os.path.dirname(photo.image.path)
                directories_to_clean.add(review_dir)

    # The individual photo deletion signals will handle file cleanup
    # We'll clean up the main location directory structure after cascade deletion
    if directories_to_clean:
        # Schedule directory cleanup (this will run after individual deletions)
        for dir_path in directories_to_clean:
            # Individual signals will handle this, but we log the location deletion
            logger.info(f"Location {instance.id} deleted - media cleanup handled by cascade signals")


@receiver(post_delete, sender=ViewingLocation)
def cleanup_location_directory_structure(sender, instance, **kwargs):
    """
    Clean up the entire location directory structure after all cascade deletions are complete.
    """
    try:
        # Try to clean up the main review photos directory
        review_photos_dir = os.path.join(settings.MEDIA_ROOT, 'review_photos', str(instance.id))

        safe_delete_directory(review_photos_dir)

        logger.info(f"Cleaned up directory structure for deleted location {instance.id}")

    except Exception as e:
        logger.error(f"Error cleaning up directory structure for location {instance.id}: {str(e)}")


@receiver(post_delete, sender=LocationReview)
def cleanup_review_directory_structure(sender, instance, **kwargs):
    """
    Clean up the review directory structure after all cascade deletions are complete.
    """
    try:
        # Try to clean up the main review directory
        review_dir = os.path.join(
            settings.MEDIA_ROOT,
            'review_photos',
            str(instance.location.id),
            str(instance.id)
        )

        safe_delete_directory(review_dir)

        logger.info(f"Cleaned up directory structure for deleted review {instance.id}")

    except Exception as e:
        logger.error(f"Error cleaning up directory structure for review {instance.id}: {str(e)}")
