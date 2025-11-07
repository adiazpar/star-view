# ----------------------------------------------------------------------------------------------------- #
# This validators.py file provides reusable validation utilities for data integrity and security.       #
#                                                                                                       #
# Purpose:                                                                                              #
# Centralized validation functions for file uploads, geographic coordinates, password strength,         #
# and input sanitization. These validators are used across views, serializers, and models to ensure     #
# consistent validation logic throughout the application.                                               #
#                                                                                                       #
# Key Features:                                                                                         #
# - File upload validation: size limits, MIME types, extensions, malicious content detection            #
# - Geographic validation: latitude/longitude bounds, elevation ranges                                  #
# - Password validation: uppercase, number, special character requirements                              #
# - XSS prevention: HTML sanitization with bleach (strips dangerous tags, allows safe formatting)       #
# - Reusable across models, serializers, and views                                                      #
# - Raises Django ValidationError for consistent error handling                                         #
#                                                                                                       #
# Architecture:                                                                                         #
# - Pure functions with no side effects (easier to test and reason about)                               #
# - Uses Django's ValidationError for framework integration                                             #
# - Settings-driven configuration (max file size, allowed types from settings.py)                       #
# ----------------------------------------------------------------------------------------------------- #

import os
import re
import mimetypes
import bleach
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext as _


# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                    FILE UPLOAD VALIDATION                                             #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Validate uploaded file size is within the configured maximum limit.           #
#                                                                               #
# Prevents DOS attacks via large file uploads and storage exhaustion. Reads     #
# file size from the uploaded file object without loading entire file into      #
# memory for efficiency.                                                        #
#                                                                               #
# Args:     file: UploadedFile object from request.FILES                        #
#           max_mb: Maximum file size in megabytes (default from settings)      #
# Raises:   ValidationError if file exceeds size limit                          #
# ----------------------------------------------------------------------------- #
def validate_file_size(file, max_mb=None):
    if max_mb is None:
        max_mb = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 5)

    max_bytes = max_mb * 1024 * 1024  # Convert MB to bytes

    if file.size > max_bytes:
        raise ValidationError(
            f'File size ({file.size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({max_mb}MB).'
        )


# ----------------------------------------------------------------------------- #
# Validate uploaded file is a legitimate image file.                            #
#                                                                               #
# Performs multiple security checks:                                            #
# 1. File extension whitelist check (prevents .exe, .php, etc.)                 #
# 2. MIME type validation (checks actual content type, not just extension)      #
# 3. Content validation using Pillow to verify it's actually an image           #
#                                                                               #
# This multi-layer approach prevents attackers from uploading malicious files   #
# disguised as images (e.g., PHP script named "hack.jpg").                      #
#                                                                               #
# Args:     file: UploadedFile object from request.FILES                        #
# Raises:   ValidationError if file is not a valid image                        #
# ----------------------------------------------------------------------------- #
def validate_image_file(file):
    # Import here to avoid circular imports and keep PIL optional for non-image validators
    from PIL import Image

    # Get allowed extensions and MIME types from settings
    allowed_extensions = getattr(
        settings,
        'ALLOWED_IMAGE_EXTENSIONS',
        ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    )
    allowed_mimetypes = getattr(
        settings,
        'ALLOWED_IMAGE_MIMETYPES',
        ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    )

    # 1. Validate file extension (using dedicated validator)
    validate_file_extension(file.name, allowed_extensions)

    # 2. Validate MIME type from content
    # Use content_type from upload if available, otherwise guess from filename
    content_type = file.content_type if hasattr(file, 'content_type') else None

    if not content_type:
        # Fallback: guess MIME type from filename
        content_type, _ = mimetypes.guess_type(file.name)

    if content_type not in allowed_mimetypes:
        raise ValidationError(
            f'Invalid file type "{content_type}". Only image files are allowed.'
        )

    # 3. Validate actual image content using Pillow
    # This catches files with image extensions but non-image content
    try:
        # Attempt to open and verify the image
        image = Image.open(file)
        image.verify()  # Verify it's actually an image

        # Reset file pointer after verify() (verify consumes the file)
        file.seek(0)

    except Exception as e:
        raise ValidationError(
            f'Invalid image file. The file may be corrupted or not a real image.'
        )


# ----------------------------------------------------------------------------- #
# Validate filename extension against a whitelist.                              #
#                                                                               #
# Generic extension validator that can be used for any file type. Provides      #
# defense-in-depth when combined with MIME type validation.                     #
#                                                                               #
# Args:     filename: Name of the uploaded file                                 #
#           allowed_extensions: List of allowed extensions (e.g., ['.jpg'])     #
# Raises:   ValidationError if extension not in whitelist                       #
# ----------------------------------------------------------------------------- #
def validate_file_extension(filename, allowed_extensions):
    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_extensions:
        raise ValidationError(
            f'File extension "{ext}" not allowed. Allowed extensions: {", ".join(allowed_extensions)}'
        )


# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                GEOGRAPHIC COORDINATE VALIDATION                                       #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Validate latitude is within valid geographic bounds.                          #
#                                                                               #
# Latitude ranges from -90° (South Pole) to +90° (North Pole). Values outside   #
# this range are physically impossible and likely indicate data corruption,     #
# injection attempts, or client-side validation bypass.                         #
#                                                                               #
# Args:     value: Latitude value to validate                                   #
# Raises:   ValidationError if latitude is out of bounds                        #
# ----------------------------------------------------------------------------- #
def validate_latitude(value):
    if value < -90 or value > 90:
        raise ValidationError(
            f'Latitude must be between -90 and 90 degrees. Got: {value}'
        )


# ----------------------------------------------------------------------------- #
# Validate longitude is within valid geographic bounds.                         #
#                                                                               #
# Longitude ranges from -180° to +180°. Values outside this range wrap around   #
# but should still be rejected as they indicate improper normalization.         #
#                                                                               #
# Args:     value: Longitude value to validate                                  #
# Raises:   ValidationError if longitude is out of bounds                       #
# ----------------------------------------------------------------------------- #
def validate_longitude(value):
    if value < -180 or value > 180:
        raise ValidationError(
            f'Longitude must be between -180 and 180 degrees. Got: {value}'
        )


# ----------------------------------------------------------------------------- #
# Validate elevation is within reasonable bounds.                               #
#                                                                               #
# Elevation ranges from approximately -500m (Dead Sea, deepest depression) to   #
# ~9000m (Mount Everest peak). Values outside this range are unrealistic for    #
# stargazing locations and likely indicate data errors.                         #
#                                                                               #
# Args:     value: Elevation in meters to validate                              #
# Raises:   ValidationError if elevation is unrealistic                         #
# ----------------------------------------------------------------------------- #
def validate_elevation(value):
    if value < -500 or value > 9000:
        raise ValidationError(
            f'Elevation must be between -500m and 9000m. Got: {value}m'
        )



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                    INPUT SANITIZATION (XSS PREVENTION)                                #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Sanitize user-generated text content to prevent XSS attacks.                  #
#                                                                               #
# Uses bleach library to strip dangerous HTML/JavaScript while allowing safe    #
# formatting tags. This prevents stored XSS attacks where malicious scripts     #
# are saved to the database and executed in other users' browsers.              #
#                                                                               #
# Allowed tags: <b>, <i>, <u>, <em>, <strong>, <br>, <p>                        #
# Blocked tags: <script>, <iframe>, <object>, event handlers (onclick, etc.)    #
#                                                                               #
# Args:     value: Text content to sanitize (str)                               #
# Returns:  Sanitized text with dangerous content removed (str)                 #
# ----------------------------------------------------------------------------- #
def sanitize_html(value):

    if not value:
        return value

    # First, remove script and style tags entirely (including their content)
    import re
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.DOTALL | re.IGNORECASE)
    value = re.sub(r'<style[^>]*>.*?</style>', '', value, flags=re.DOTALL | re.IGNORECASE)

    # Define allowed HTML tags (safe formatting only)
    allowed_tags = [
        'b', 'i', 'u', 'em', 'strong', 'br', 'p',
        'ul', 'ol', 'li', 'blockquote', 'code'
    ]

    # Define allowed attributes (very restrictive)
    # No event handlers (onclick, onerror, etc.) allowed
    allowed_attributes = {}

    # Strip all dangerous content (removes disallowed tags but keeps their text)
    sanitized = bleach.clean(
        value,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True,  # Strip disallowed tags (but keep text content)
        strip_comments=True  # Remove HTML comments
    )

    return sanitized


# ----------------------------------------------------------------------------- #
# Sanitize plain text content (no HTML allowed at all).                         #
#                                                                               #
# For fields where HTML formatting isn't needed (like location names), this     #
# strips ALL HTML tags to ensure only plain text is stored. More restrictive    #
# than sanitize_html().                                                         #
#                                                                               #
# Args:     value: Text content to sanitize (str)                               #
# Returns:  Plain text with all HTML removed (str)                              #
# ----------------------------------------------------------------------------- #
def sanitize_plain_text(value):
    if not value:
        return value

    # First, remove script and style tags entirely (including their content)
    import re
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.DOTALL | re.IGNORECASE)
    value = re.sub(r'<style[^>]*>.*?</style>', '', value, flags=re.DOTALL | re.IGNORECASE)

    # Strip all HTML tags, no exceptions
    sanitized = bleach.clean(
        value,
        tags=[],  # No tags allowed
        attributes={},
        strip=True,
        strip_comments=True
    )

    return sanitized


# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                    PASSWORD STRENGTH VALIDATION                                       #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Validate password contains at least one uppercase letter.                     #
#                                                                               #
# Enforces password complexity by requiring uppercase letters. This increases   #
# password entropy and makes brute-force attacks more difficult.                #
#                                                                               #
# Args:     password: Password string to validate                               #
#           user: User object (optional, for compatibility with Django)         #
# Raises:   ValidationError if no uppercase letter found                        #
# ----------------------------------------------------------------------------- #
class UppercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least 1 uppercase letter."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _("Your password must contain at least 1 uppercase letter.")


# ----------------------------------------------------------------------------- #
# Validate password contains at least one number.                               #
#                                                                               #
# Enforces password complexity by requiring digits. Combining letters and       #
# numbers significantly increases the password search space for attackers.      #
#                                                                               #
# Args:     password: Password string to validate                               #
#           user: User object (optional, for compatibility with Django)         #
# Raises:   ValidationError if no digit found                                   #
# ----------------------------------------------------------------------------- #
class NumberValidator:
    def validate(self, password, user=None):
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least 1 number."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _("Your password must contain at least 1 number.")


# ----------------------------------------------------------------------------- #
# Validate password contains at least one special character.                    #
#                                                                               #
# Enforces password complexity by requiring special characters. This provides   #
# additional entropy and protects against dictionary attacks and common         #
# password patterns.                                                            #
#                                                                               #
# Special characters: !@#$%^&*(),.?":{}|<>                                      #
#                                                                               #
# Args:     password: Password string to validate                               #
#           user: User object (optional, for compatibility with Django)         #
# Raises:   ValidationError if no special character found                       #
# ----------------------------------------------------------------------------- #
class SpecialCharacterValidator:
    def validate(self, password, user=None):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least 1 special character (!@#$%^&*(),.?\":{}|<>)."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _("Your password must contain at least 1 special character (!@#$%^&*(),.?\":{}|<>).")
