# ----------------------------------------------------------------------------------------------------- #
# This report_service.py file handles report submission operations for reviews and comments:            #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides centralized business logic for reporting inappropriate content using Django's ContentTypes   #
# framework. Eliminates code duplication between ReviewViewSet and CommentViewSet.                      #
#                                                                                                       #
# Key Features:                                                                                         #
# - Validation Logic: Prevents users from reporting their own content                                   #
# - Duplicate Prevention: Checks if user already reported the same content                              #
# - Generic Support: Works with any content type via ContentTypes framework                             #
# - Error Handling: Returns structured success/error responses                                          #
#                                                                                                       #
# Service Layer Pattern:                                                                                #
# This service separates business logic from views, following Django best practices:                    #
# - Models define data structure (Report model)                                                         #
# - Services define business logic (report validation and submission)                                   #
# - Views coordinate between user requests and services                                                 #
#                                                                                                       #
# Usage:                                                                                                #
# - All methods are static and can be called independently                                              #
# - Used by ReviewViewSet and CommentViewSet for consistent report handling                             #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.contrib.contenttypes.models import ContentType
from stars_app.models.model_report import Report


class ReportService:

    # ----------------------------------------------------------------------------- #
    # Submit a report for any content object (review, comment, location, etc.).     #
    #                                                                               #
    # Report Submission Logic:                                                      #
    # 1. Validate user is not reporting their own content                           #
    # 2. Check for duplicate reports from the same user                             #
    # 3. Create and save the report with ContentTypes framework                     #
    #                                                                               #
    # Args:     user (User): The user submitting the report                         #
    #           content_object: The object being reported (Review, Comment, etc.)   #
    #           report_type (str): Type of report (e.g., 'SPAM', 'INAPPROPRIATE')   #
    #           description (str): User's description of the issue                  #
    # Returns:  Report: The created Report instance                                 #
    # Raises:   ValidationError: If validation fails                                #
    # ----------------------------------------------------------------------------- #
    @staticmethod
    def submit_report(user, content_object, report_type='OTHER', description=''):
        # Import here to avoid circular dependency
        from stars_app.serializers import ReportSerializer
        from rest_framework.exceptions import ValidationError

        # Prevent users from reporting their own content
        # Check both 'user' and 'added_by' fields (different models use different names)
        content_owner = None
        if hasattr(content_object, 'user'):
            content_owner = content_object.user
        elif hasattr(content_object, 'added_by'):
            content_owner = content_object.added_by

        if content_owner and content_owner == user:
            raise ValidationError('You cannot report your own content')

        # Get the ContentType for the content object
        content_type = ContentType.objects.get_for_model(content_object)

        # Check if user already reported this content
        existing_report = Report.objects.filter(
            content_type=content_type,
            object_id=content_object.id,
            reported_by=user
        ).first()

        if existing_report:
            content_type_name = content_type.model.replace('_', ' ')
            raise ValidationError(f'You have already reported this {content_type_name}')

        # Prepare report data for the generic Report model
        report_data = {
            'report_type': report_type,
            'description': description
        }

        # Validate and save the report
        serializer = ReportSerializer(data=report_data)
        if serializer.is_valid():
            report = serializer.save(
                content_type=content_type,
                object_id=content_object.id,
                reported_by=user
            )
            return report
        else:
            # Raise ValidationError with serializer errors
            raise ValidationError(serializer.errors)


    # ----------------------------------------------------------------------------- #
    # Check if a user has already reported a specific content object.               #
    #                                                                               #
    # Useful for displaying report status in UI without submitting a report.        #
    #                                                                               #
    # Args:     user (User): The user to check                                      #
    #           content_object: The object to check for existing reports            #
    # Returns:  bool: True if user has already reported this content                #
    # ----------------------------------------------------------------------------- #
    @staticmethod
    def has_user_reported(user, content_object):
        try:
            if not user or not user.is_authenticated:
                return False

            content_type = ContentType.objects.get_for_model(content_object)
            return Report.objects.filter(
                content_type=content_type,
                object_id=content_object.id,
                reported_by=user
            ).exists()

        except Exception:
            return False
