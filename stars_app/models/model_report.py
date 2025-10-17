from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Report(models.Model):
    """
    Generic report model that can handle reports for ANY type of content.

    This model uses Django's ContentTypes framework with a GenericForeignKey
    to create a truly generic relationship. A Report can point to any model:
    - ViewingLocation
    - LocationReview
    - ReviewComment
    - Or any future models you want to make reportable

    The GenericForeignKey works by storing:
    1. content_type: Which model is being reported (e.g., "LocationReview")
    2. object_id: The ID of that specific object
    3. reported_object: A virtual field that combines the above two
    """

    # ==================== TIMESTAMP FIELDS ====================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # ==================== GENERIC RELATIONSHIP ====================
    # These three fields work together to create a generic relationship
    # that can point to ANY model in your Django project

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of object being reported (e.g., ViewingLocation, LocationReview, etc.)"
    )

    object_id = models.PositiveIntegerField(
        help_text="The ID of the specific object being reported"
    )

    reported_object = GenericForeignKey('content_type', 'object_id')
    # This is a virtual field that combines content_type + object_id
    # Usage: report.reported_object will return the actual object (location/review/comment)


    # ==================== REPORT METADATA FIELDS ====================

    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submitted_reports',
        help_text="The user who submitted this report"
    )

    # All possible report types - works for any content type
    REPORT_TYPES = [
        # Content-based report types (apply to reviews and comments)
        ('SPAM', 'Spam or Low Quality'),
        ('HARASSMENT', 'Harassment or Bullying'),
        ('INAPPROPRIATE', 'Inappropriate Content'),
        ('MISINFORMATION', 'False or Misleading Information'),

        # Location-specific report types
        ('DUPLICATE', 'Duplicate Location'),
        ('INACCURATE', 'Inaccurate Information'),
        ('CLOSED', 'Location Closed/Inaccessible'),
        ('DANGEROUS', 'Safety Concerns'),

        # Generic catch-all
        ('OTHER', 'Other'),
    ]

    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        help_text="The type/reason for this report"
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed description of the issue being reported"
    )

    # Status tracking for moderation workflow
    REPORT_STATUS = [
        ('PENDING', 'Pending Review'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]

    status = models.CharField(
        max_length=20,
        choices=REPORT_STATUS,
        default='PENDING',
        help_text="Current status in the moderation workflow"
    )


    # ==================== ADDITIONAL DATA ====================
    # JSONField for storing any extra context data
    # Examples:
    # - For duplicate reports: {"duplicate_of_id": 123}
    # - For inaccurate reports: {"incorrect_fields": ["elevation", "address"]}
    # - Any custom data specific to certain report types

    additional_data = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Optional JSON field for storing additional context (e.g., duplicate location ID)"
    )


    # ==================== MODERATION FIELDS ====================

    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_reports',
        help_text="The moderator who reviewed this report"
    )

    review_notes = models.TextField(
        blank=True,
        help_text="Internal notes from the moderator about their decision"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this report was reviewed by a moderator"
    )


    # ==================== MODEL CONFIGURATION ====================

    class Meta:
        ordering = ['-created_at']

        # Database indexes for common queries
        indexes = [
            # Speed up queries filtering by content type and status
            models.Index(fields=['content_type', 'object_id', 'status']),

            # Speed up queries for user's reports
            models.Index(fields=['reported_by', '-created_at']),

            # Speed up moderation queue queries
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['report_type', '-created_at']),
        ]


    # ==================== HELPER PROPERTIES ====================

    @property
    def reported_object_type(self):
        """
        Returns a string indicating what type of object is being reported.

        Returns:
            The model name as a string (e.g., 'viewinglocation', 'locationreview', 'reviewcomment')

        Usage:
            if report.reported_object_type == 'viewinglocation':
                # Handle location-specific logic
        """
        if self.content_type:
            return self.content_type.model
        return None


    # ==================== STRING REPRESENTATION ====================

    def __str__(self):
        """
        Human-readable string representation for admin interface and debugging.
        """
        type_display = self.get_report_type_display()

        if self.reported_object:
            # Try to get a meaningful string representation
            target = str(self.reported_object)
        else:
            target = f"{self.content_type.model} #{self.object_id}"

        return f"{type_display} report for {target}"
