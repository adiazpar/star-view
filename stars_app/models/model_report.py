# ----------------------------------------------------------------------------------------------------- #
# This model_report.py file defines the Report model:                                                   #
#                                                                                                       #
# Purpose:                                                                                              #
# Generic reporting system using Django's ContentTypes framework. Allows users to report any type of    #
# content with a single unified model and moderation workflow.                                          #
#                                                                                                       #
# Key Features:                                                                                         #
# - GenericForeignKey: Can point to any model (Location, Review, ReviewComment, etc.)                   #
# - Flexible report types: Spam, Duplicate, Harassment, Inaccurate, etc.                                #
# - Moderation workflow: PENDING → REVIEWED → RESOLVED/DISMISSED status tracking                        #
# - Additional data: JSONField for extra context (e.g., duplicate_of_id)                                #
# - Audit trail: Tracks who reported, who reviewed, and when                                            #
#                                                                                                       #
# ContentTypes Framework:                                                                               #
# Uses three fields to create generic relationships:                                                    #
# 1. content_type → Which model (e.g., "Review", "Location")                                            #
# 2. object_id → Specific instance ID                                                                   #
# 3. reported_object → Virtual field combining the above (GenericForeignKey)                            #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType



class Report(models.Model):
    # Timestamps:
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Generic relationship (ContentTypes framework):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, help_text="Type of object being reported")
    object_id = models.PositiveIntegerField(help_text="ID of the specific object being reported")
    reported_object = GenericForeignKey('content_type', 'object_id')  # Virtual field combining above

    # Report metadata:
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports', help_text="User who submitted this report")

    REPORT_TYPES = [
        ('SPAM', 'Spam or Low Quality'),
        ('HARASSMENT', 'Harassment or Bullying'),
        ('INAPPROPRIATE', 'Inappropriate Content'),
        ('MISINFORMATION', 'False or Misleading Information'),
        ('DUPLICATE', 'Duplicate Location'),
        ('INACCURATE', 'Inaccurate Information'),
        ('CLOSED', 'Location Closed/Inaccessible'),
        ('DANGEROUS', 'Safety Concerns'),
        ('OTHER', 'Other'),
    ]

    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, help_text="Type/reason for this report")
    description = models.TextField(blank=True, help_text="Detailed description of the issue")

    REPORT_STATUS = [
        ('PENDING', 'Pending Review'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]

    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='PENDING', help_text="Current status in moderation workflow")

    # Additional context data (e.g., {"duplicate_of_id": 123}):
    additional_data = models.JSONField(null=True, blank=True, default=dict, help_text="Optional JSON for additional context")

    # Moderation tracking:
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_reports', help_text="Moderator who reviewed this report")
    review_notes = models.TextField(blank=True, help_text="Internal moderator notes")
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="When this report was reviewed")


    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'status']),
            models.Index(fields=['reported_by', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['report_type', '-created_at']),
        ]


    # Returns the model name of the reported object (e.g., 'location', 'review', 'reviewcomment'):
    @property
    def reported_object_type(self):
        if self.content_type:
            return self.content_type.model
        return None


    # String representation for admin interface and debugging:
    def __str__(self):
        type_display = self.get_report_type_display()
        target = str(self.reported_object) if self.reported_object else f"{self.content_type.model} #{self.object_id}"
        return f"{type_display} report for {target}"
