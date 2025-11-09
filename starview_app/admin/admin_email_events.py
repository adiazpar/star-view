# ----------------------------------------------------------------------------------------------------- #
# Django Admin - Email Event Management                                                                #
#                                                                                                       #
# Purpose:                                                                                              #
# Admin interfaces for viewing and managing email bounces, complaints, and suppression list.           #
# Provides dashboards for monitoring email deliverability and sender reputation.                       #
# ----------------------------------------------------------------------------------------------------- #

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from starview_app.models import EmailBounce, EmailComplaint, EmailSuppressionList


@admin.register(EmailBounce)
class EmailBounceAdmin(admin.ModelAdmin):
    """
    Admin interface for email bounces.

    Features:
    - Filter by bounce type, suppression status
    - Search by email address
    - View detailed bounce information
    - Bulk actions for suppression management
    """

    list_display = [
        'email',
        'user_link',
        'bounce_type_badge',
        'bounce_count',
        'last_bounce_date',
        'suppressed_badge',
    ]

    list_filter = [
        'bounce_type',
        'suppressed',
        'bounce_subtype',
        ('last_bounce_date', admin.DateFieldListFilter),
    ]

    search_fields = [
        'email',
        'user__username',
        'user__email',
    ]

    readonly_fields = [
        'email',
        'user',
        'bounce_type',
        'bounce_subtype',
        'bounce_count',
        'first_bounce_date',
        'last_bounce_date',
        'sns_message_id',
        'diagnostic_code_display',
        'raw_notification_display',
    ]

    fieldsets = (
        ('Email Information', {
            'fields': ('email', 'user')
        }),
        ('Bounce Details', {
            'fields': (
                'bounce_type',
                'bounce_subtype',
                'bounce_count',
                'first_bounce_date',
                'last_bounce_date',
            )
        }),
        ('AWS Details', {
            'fields': (
                'sns_message_id',
                'diagnostic_code_display',
            )
        }),
        ('Status', {
            'fields': ('suppressed',)
        }),
        ('Raw Data', {
            'fields': ('raw_notification_display',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_suppressed', 'remove_from_suppression']

    def user_link(self, obj):
        """Link to user admin page."""
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return '-'
    user_link.short_description = 'User'

    def bounce_type_badge(self, obj):
        """Colored badge for bounce type."""
        colors = {
            'hard': 'red',
            'soft': 'orange',
            'transient': 'gray',
        }
        color = colors.get(obj.bounce_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.bounce_type.upper()
        )
    bounce_type_badge.short_description = 'Type'

    def suppressed_badge(self, obj):
        """Colored badge for suppression status."""
        if obj.suppressed:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">SUPPRESSED</span>'
            )
        return format_html(
            '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">ACTIVE</span>'
        )
    suppressed_badge.short_description = 'Status'

    def diagnostic_code_display(self, obj):
        """Display diagnostic code with formatting."""
        if obj.diagnostic_code:
            return format_html('<pre>{}</pre>', obj.diagnostic_code)
        return '-'
    diagnostic_code_display.short_description = 'Diagnostic Code'

    def raw_notification_display(self, obj):
        """Display raw notification JSON with formatting."""
        import json
        return format_html(
            '<pre>{}</pre>',
            json.dumps(obj.raw_notification, indent=2)
        )
    raw_notification_display.short_description = 'Raw SNS Notification'

    def mark_as_suppressed(self, request, queryset):
        """Add bounced emails to suppression list."""
        count = 0
        for bounce in queryset:
            if not bounce.suppressed:
                EmailSuppressionList.add_to_suppression(
                    email=bounce.email,
                    reason='hard_bounce' if bounce.bounce_type == 'hard' else 'soft_bounce',
                    bounce=bounce,
                    notes=f'Manually suppressed by admin via bulk action'
                )
                bounce.suppressed = True
                bounce.save()
                count += 1

        self.message_user(request, f'{count} email(s) added to suppression list.')
    mark_as_suppressed.short_description = 'Add to suppression list'

    def remove_from_suppression(self, request, queryset):
        """Remove emails from suppression list."""
        count = 0
        for bounce in queryset:
            if bounce.suppressed:
                # Deactivate suppression
                EmailSuppressionList.objects.filter(
                    email=bounce.email,
                    is_active=True
                ).update(is_active=False)

                bounce.suppressed = False
                bounce.save()
                count += 1

        self.message_user(request, f'{count} email(s) removed from suppression list.')
    remove_from_suppression.short_description = 'Remove from suppression list'


@admin.register(EmailComplaint)
class EmailComplaintAdmin(admin.ModelAdmin):
    """
    Admin interface for email complaints.

    Features:
    - Filter by complaint type, review status
    - Search by email address
    - View detailed complaint information
    - Mark complaints as reviewed
    """

    list_display = [
        'email',
        'user_link',
        'complaint_type_badge',
        'complaint_date',
        'reviewed_badge',
        'suppressed_badge',
    ]

    list_filter = [
        'complaint_type',
        'reviewed',
        'suppressed',
        ('complaint_date', admin.DateFieldListFilter),
    ]

    search_fields = [
        'email',
        'user__username',
        'user__email',
    ]

    readonly_fields = [
        'email',
        'user',
        'complaint_type',
        'complaint_date',
        'user_agent',
        'sns_message_id',
        'feedback_id',
        'raw_notification_display',
    ]

    fieldsets = (
        ('Email Information', {
            'fields': ('email', 'user')
        }),
        ('Complaint Details', {
            'fields': (
                'complaint_type',
                'complaint_date',
                'user_agent',
            )
        }),
        ('AWS Details', {
            'fields': (
                'sns_message_id',
                'feedback_id',
            )
        }),
        ('Status', {
            'fields': ('suppressed', 'reviewed')
        }),
        ('Raw Data', {
            'fields': ('raw_notification_display',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_reviewed', 'mark_as_unreviewed']

    def user_link(self, obj):
        """Link to user admin page."""
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return '-'
    user_link.short_description = 'User'

    def complaint_type_badge(self, obj):
        """Colored badge for complaint type."""
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            obj.complaint_type.upper()
        )
    complaint_type_badge.short_description = 'Type'

    def reviewed_badge(self, obj):
        """Badge for review status."""
        if obj.reviewed:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">REVIEWED</span>'
            )
        return format_html(
            '<span style="background-color: orange; color: white; padding: 3px 10px; border-radius: 3px;">PENDING</span>'
        )
    reviewed_badge.short_description = 'Review Status'

    def suppressed_badge(self, obj):
        """Badge for suppression status."""
        if obj.suppressed:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">SUPPRESSED</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">NOT SUPPRESSED</span>'
        )
    suppressed_badge.short_description = 'Status'

    def raw_notification_display(self, obj):
        """Display raw notification JSON with formatting."""
        import json
        return format_html(
            '<pre>{}</pre>',
            json.dumps(obj.raw_notification, indent=2)
        )
    raw_notification_display.short_description = 'Raw SNS Notification'

    def mark_as_reviewed(self, request, queryset):
        """Mark complaints as reviewed."""
        count = queryset.update(reviewed=True)
        self.message_user(request, f'{count} complaint(s) marked as reviewed.')
    mark_as_reviewed.short_description = 'Mark as reviewed'

    def mark_as_unreviewed(self, request, queryset):
        """Mark complaints as unreviewed."""
        count = queryset.update(reviewed=False)
        self.message_user(request, f'{count} complaint(s) marked as unreviewed.')
    mark_as_unreviewed.short_description = 'Mark as unreviewed'


@admin.register(EmailSuppressionList)
class EmailSuppressionListAdmin(admin.ModelAdmin):
    """
    Admin interface for email suppression list.

    Features:
    - Filter by reason, active status
    - Search by email address
    - Bulk activate/deactivate suppressions
    - View linked bounce/complaint records
    """

    list_display = [
        'email',
        'user_link',
        'reason_badge',
        'added_date',
        'is_active_badge',
    ]

    list_filter = [
        'reason',
        'is_active',
        ('added_date', admin.DateFieldListFilter),
    ]

    search_fields = [
        'email',
        'user__username',
        'user__email',
    ]

    readonly_fields = [
        'added_date',
        'bounce_link',
        'complaint_link',
    ]

    fieldsets = (
        ('Email Information', {
            'fields': ('email', 'user')
        }),
        ('Suppression Details', {
            'fields': (
                'reason',
                'added_date',
                'notes',
            )
        }),
        ('Linked Records', {
            'fields': (
                'bounce_link',
                'complaint_link',
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    actions = ['activate_suppression', 'deactivate_suppression']

    def user_link(self, obj):
        """Link to user admin page."""
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return '-'
    user_link.short_description = 'User'

    def reason_badge(self, obj):
        """Colored badge for suppression reason."""
        colors = {
            'hard_bounce': 'red',
            'soft_bounce': 'orange',
            'complaint': 'darkred',
            'manual': 'blue',
            'unsubscribe': 'green',
        }
        color = colors.get(obj.reason, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_reason_display()
        )
    reason_badge.short_description = 'Reason'

    def is_active_badge(self, obj):
        """Badge for active status."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">ACTIVE</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">INACTIVE</span>'
        )
    is_active_badge.short_description = 'Status'

    def bounce_link(self, obj):
        """Link to related bounce record."""
        if obj.bounce:
            return format_html(
                '<a href="/admin/starview_app/emailbounce/{}/change/">View Bounce #{}</a>',
                obj.bounce.id,
                obj.bounce.id
            )
        return '-'
    bounce_link.short_description = 'Related Bounce'

    def complaint_link(self, obj):
        """Link to related complaint record."""
        if obj.complaint:
            return format_html(
                '<a href="/admin/starview_app/emailcomplaint/{}/change/">View Complaint #{}</a>',
                obj.complaint.id,
                obj.complaint.id
            )
        return '-'
    complaint_link.short_description = 'Related Complaint'

    def activate_suppression(self, request, queryset):
        """Activate suppression for selected emails."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} suppression(s) activated.')
    activate_suppression.short_description = 'Activate suppression'

    def deactivate_suppression(self, request, queryset):
        """Deactivate suppression for selected emails."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} suppression(s) deactivated.')
    deactivate_suppression.short_description = 'Deactivate suppression'
