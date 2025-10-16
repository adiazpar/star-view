from django.db import models
from django.contrib.auth.models import User
from .model_base import TimestampedModel
from .model_viewing_location import ViewingLocation


class LocationReport(TimestampedModel):
    """Reports submitted by users about viewing locations"""
    
    REPORT_TYPES = [
        ('DUPLICATE', 'Duplicate Location'),
        ('INACCURATE', 'Inaccurate Information'),
        ('SPAM', 'Spam or Inappropriate'),
        ('CLOSED', 'Location Closed/Inaccessible'),
        ('DANGEROUS', 'Safety Concerns'),
        ('OTHER', 'Other'),
    ]
    
    REPORT_STATUS = [
        ('PENDING', 'Pending Review'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]
    
    location = models.ForeignKey(
        ViewingLocation,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='location_reports'
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        help_text="Type of report"
    )
    description = models.TextField(
        help_text="Detailed description of the issue"
    )
    status = models.CharField(
        max_length=20,
        choices=REPORT_STATUS,
        default='PENDING',
        help_text="Current status of the report"
    )
    duplicate_of = models.ForeignKey(
        ViewingLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duplicate_reports',
        help_text="If duplicate, which location is this a duplicate of"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports',
        help_text="Moderator who reviewed this report"
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Notes from the moderator review"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the report was reviewed"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['location', 'status']),
            models.Index(fields=['reported_by', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
        # Prevent duplicate reports from same user
        unique_together = [['location', 'reported_by', 'report_type']]
    
    def __str__(self):
        return f"{self.get_report_type_display()} report for {self.location.name}"