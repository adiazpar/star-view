# ----------------------------------------------------------------------------------------------------- #
# Email Event Models - AWS SES Bounce and Complaint Tracking                                           #
#                                                                                                       #
# Purpose:                                                                                              #
# Tracks email bounces, complaints, and maintains suppression lists for AWS SES integration.           #
# Receives real-time notifications from AWS SNS webhooks when emails bounce or are marked as spam.     #
#                                                                                                       #
# Models:                                                                                               #
# - EmailBounce: Tracks bounced emails (hard/soft/transient)                                           #
# - EmailComplaint: Tracks spam complaints from recipients                                             #
# - EmailSuppressionList: Master list of emails that should never receive emails                       #
#                                                                                                       #
# Integration:                                                                                          #
# AWS SES → AWS SNS → Django webhook endpoints → These models                                          #
# Prevents sending to problematic addresses, maintains sender reputation                               #
# ----------------------------------------------------------------------------------------------------- #

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class EmailBounce(models.Model):
    """
    Tracks email bounces from AWS SES.

    Bounce Types:
    - Hard: Permanent delivery failure (invalid email, domain doesn't exist)
    - Soft: Temporary failure (mailbox full, server temporarily unavailable)
    - Transient: Temporary issue (connection timeout, throttling)

    Action Rules:
    - Hard bounce: Immediate suppression, never send again
    - Soft bounce (3+ times): Add to suppression list
    - Transient: Monitor only, no suppression
    """

    BOUNCE_TYPE_CHOICES = [
        ('hard', 'Hard Bounce (Permanent)'),
        ('soft', 'Soft Bounce (Temporary)'),
        ('transient', 'Transient (Connection Issue)'),
    ]

    BOUNCE_SUBTYPE_CHOICES = [
        ('undetermined', 'Undetermined'),
        ('general', 'General'),
        ('no_email', 'Mailbox Does Not Exist'),
        ('suppressed', 'Address Suppressed'),
        ('mailbox_full', 'Mailbox Full'),
        ('message_too_large', 'Message Too Large'),
        ('content_rejected', 'Content Rejected'),
        ('attachment_rejected', 'Attachment Rejected'),
    ]

    # Email information
    email = models.EmailField(db_index=True, help_text="Email address that bounced")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_bounces',
        help_text="User associated with this email (if exists)"
    )

    # Bounce details
    bounce_type = models.CharField(
        max_length=20,
        choices=BOUNCE_TYPE_CHOICES,
        db_index=True,
        help_text="Type of bounce (hard/soft/transient)"
    )
    bounce_subtype = models.CharField(
        max_length=50,
        choices=BOUNCE_SUBTYPE_CHOICES,
        default='undetermined',
        help_text="Specific reason for bounce"
    )

    # Tracking
    bounce_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of times this email has bounced"
    )
    first_bounce_date = models.DateTimeField(
        auto_now_add=True,
        help_text="First time this email bounced"
    )
    last_bounce_date = models.DateTimeField(
        auto_now=True,
        help_text="Most recent bounce"
    )

    # AWS metadata
    sns_message_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="AWS SNS message ID for deduplication"
    )
    diagnostic_code = models.TextField(
        blank=True,
        help_text="SMTP diagnostic message from receiving server"
    )
    raw_notification = models.JSONField(
        help_text="Complete SNS notification payload"
    )

    # Status
    suppressed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this email has been added to suppression list"
    )

    class Meta:
        db_table = 'starview_email_bounce'
        verbose_name = 'Email Bounce'
        verbose_name_plural = 'Email Bounces'
        ordering = ['-last_bounce_date']
        indexes = [
            models.Index(fields=['email', '-last_bounce_date']),
            models.Index(fields=['bounce_type', 'suppressed']),
        ]

    def __str__(self):
        return f"{self.email} - {self.bounce_type} ({self.bounce_count}x)"

    def should_suppress(self):
        """
        Determine if this email should be added to suppression list.

        Rules:
        - Hard bounce: Always suppress immediately
        - Soft bounce: Suppress after 3 consecutive bounces
        - Transient: Never suppress (temporary issues)
        """
        if self.bounce_type == 'hard':
            return True
        elif self.bounce_type == 'soft' and self.bounce_count >= 3:
            return True
        return False


class EmailComplaint(models.Model):
    """
    Tracks spam complaints from AWS SES.

    When a recipient marks an email as spam, their email provider (Gmail, Yahoo, etc.)
    may report it back to AWS SES via feedback loops. This is tracked here.

    Action Rules:
    - Any complaint: Immediate suppression, never send again
    - Alert admin for manual review
    - Monitor complaint rate (must stay below 0.1%)
    """

    COMPLAINT_TYPE_CHOICES = [
        ('abuse', 'Abuse Report'),
        ('auth-failure', 'Authentication Failure'),
        ('fraud', 'Fraud Report'),
        ('not-spam', 'Not Spam (False Positive)'),
        ('other', 'Other/Unknown'),
        ('virus', 'Virus Report'),
    ]

    # Email information
    email = models.EmailField(db_index=True, help_text="Email address that complained")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_complaints',
        help_text="User associated with this email (if exists)"
    )

    # Complaint details
    complaint_type = models.CharField(
        max_length=50,
        choices=COMPLAINT_TYPE_CHOICES,
        default='other',
        help_text="Type of complaint reported"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="Email client user agent (if available)"
    )

    # Tracking
    complaint_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the complaint was received"
    )

    # AWS metadata
    sns_message_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="AWS SNS message ID for deduplication"
    )
    feedback_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Feedback loop identifier from ISP"
    )
    raw_notification = models.JSONField(
        help_text="Complete SNS notification payload"
    )

    # Status
    suppressed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this email has been added to suppression list"
    )
    reviewed = models.BooleanField(
        default=False,
        help_text="Whether admin has reviewed this complaint"
    )

    class Meta:
        db_table = 'starview_email_complaint'
        verbose_name = 'Email Complaint'
        verbose_name_plural = 'Email Complaints'
        ordering = ['-complaint_date']
        indexes = [
            models.Index(fields=['email', '-complaint_date']),
            models.Index(fields=['reviewed', 'suppressed']),
        ]

    def __str__(self):
        return f"{self.email} - {self.complaint_type} on {self.complaint_date.date()}"


class EmailSuppressionList(models.Model):
    """
    Master suppression list - emails that should NEVER receive emails.

    Sources:
    - Hard bounces (permanent delivery failures)
    - Spam complaints (user marked as spam)
    - Soft bounces (3+ consecutive failures)
    - Manual admin additions

    This list is checked before every email send to prevent:
    - Wasting resources on undeliverable emails
    - Damaging sender reputation with high bounce rates
    - Legal issues from sending to unwanted recipients
    """

    REASON_CHOICES = [
        ('hard_bounce', 'Hard Bounce (Permanent Failure)'),
        ('soft_bounce', 'Soft Bounce (Multiple Failures)'),
        ('complaint', 'Spam Complaint'),
        ('manual', 'Manual Addition (Admin)'),
        ('unsubscribe', 'User Unsubscribed'),
    ]

    # Email information
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Email address to suppress"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_suppressions',
        help_text="User associated with this email (if exists)"
    )

    # Suppression details
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        help_text="Why this email was suppressed"
    )
    added_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this email was added to suppression list"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or context"
    )

    # Linked records
    bounce = models.ForeignKey(
        EmailBounce,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Related bounce record (if applicable)"
    )
    complaint = models.ForeignKey(
        EmailComplaint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Related complaint record (if applicable)"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether suppression is currently active"
    )

    class Meta:
        db_table = 'starview_email_suppression'
        verbose_name = 'Email Suppression'
        verbose_name_plural = 'Email Suppression List'
        ordering = ['-added_date']
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['reason', 'added_date']),
        ]

    def __str__(self):
        return f"{self.email} - {self.reason}"

    @classmethod
    def is_suppressed(cls, email):
        """
        Check if an email address is on the suppression list.

        Args:
            email (str): Email address to check

        Returns:
            bool: True if email should be suppressed, False otherwise
        """
        return cls.objects.filter(email=email.lower(), is_active=True).exists()

    @classmethod
    def add_to_suppression(cls, email, reason, bounce=None, complaint=None, notes=''):
        """
        Add an email to the suppression list.

        Args:
            email (str): Email address to suppress
            reason (str): Reason for suppression (from REASON_CHOICES)
            bounce (EmailBounce): Related bounce record (optional)
            complaint (EmailComplaint): Related complaint record (optional)
            notes (str): Additional notes (optional)

        Returns:
            EmailSuppressionList: Created or existing suppression record
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Find user if exists
        user = None
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            pass

        # Create or update suppression
        suppression, created = cls.objects.get_or_create(
            email=email.lower(),
            defaults={
                'user': user,
                'reason': reason,
                'bounce': bounce,
                'complaint': complaint,
                'notes': notes,
                'is_active': True,
            }
        )

        if not created and not suppression.is_active:
            # Reactivate if it was previously deactivated
            suppression.is_active = True
            suppression.reason = reason
            suppression.notes = notes
            suppression.save()

        return suppression
