from django.db import models
from django.contrib.auth.models import User
from .model_base import TimestampedModel
from .model_review_comment import ReviewComment


class CommentReport(TimestampedModel):
    """Reports submitted by users about comments"""
    
    REPORT_TYPES = [
        ('SPAM', 'Spam or Low Quality'),
        ('HARASSMENT', 'Harassment or Bullying'),
        ('INAPPROPRIATE', 'Inappropriate Content'),
        ('MISINFORMATION', 'False or Misleading Information'),
        ('OTHER', 'Other'),
    ]
    
    REPORT_STATUS = [
        ('PENDING', 'Pending Review'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]
    
    comment = models.ForeignKey(
        ReviewComment,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_reports'
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        default='OTHER',
        help_text="Type of report"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional detailed description of the issue"
    )
    status = models.CharField(
        max_length=20,
        choices=REPORT_STATUS,
        default='PENDING',
        help_text="Current status of the report"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_comment_reports',
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
            models.Index(fields=['comment', 'status']),
            models.Index(fields=['reported_by', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['report_type', '-created_at']),
        ]
        # Prevent duplicate reports from same user for same comment
        unique_together = [['comment', 'reported_by']]
    
    def __str__(self):
        return f"{self.get_report_type_display()} report for comment by {self.comment.user.username}"