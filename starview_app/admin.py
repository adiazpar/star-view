# ----------------------------------------------------------------------------------------------------- #
# This admin.py file configures the Django admin interface for the stars_app application:               #
#                                                                                                       #
# Purpose:                                                                                              #
# The Django admin interface provides a web-based interface for managing database content. This file    #
# registers models with the admin site and customizes how they appear and behave in the admin panel.    #
#                                                                                                       #
# What This Provides:                                                                                   #
# - Staff users can view, create, edit, and delete records through a web interface at /admin/           #
# - Custom admin classes enhance the default interface with better displays, filters, and search        #
# - Generic models use custom admins to handle ContentTypes framework complexity                        #
#                                                                                                       #
# Access:                                                                                               #
# Only users with is_staff=True can access the admin interface. Superusers have full permissions.       #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

# Import models:
# Separated model imports for package organization (Review system, Location system, etc.):
from .models import UserProfile, FavoriteLocation, Location, Follow
from .models import Review, ReviewComment, ReviewPhoto, Report, Vote
from .models import EmailBounce, EmailComplaint, EmailSuppressionList
from .models import AuditLog



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                       CUSTOM ADMIN INTERFACES                                         #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Custom admin interface for the generic Vote model.                            #
#                                                                               #
# The Vote model uses Django's ContentTypes framework with GenericForeignKey    #
# to handle votes for ANY type of content in a truly generic way.               #
#                                                                               #
# This admin interface makes it easy to:                                        #
# - View and filter votes by type, content type, and user                       #
# - See what object is being voted on                                           #
# - Track voting patterns across different content types                        #
# ----------------------------------------------------------------------------- #
class VoteAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'get_voted_object_type',    # Shows the model type (review, reviewcomment, etc.)
        'get_voted_object',         # Shows a human-readable description
        'user',                     # Who cast the vote
        'is_upvote',                # True for upvote, False for downvote
        'created_at',               # When the vote was cast
    ]

    list_filter = [
        'is_upvote',
        'content_type',             # Filter by model type
        'created_at',
    ]

    search_fields = [
        'user__username',
        'object_id',
    ]

    ordering = ['-created_at']
    list_per_page = 50

    fieldsets = (
        # Section 1: What's being voted on (generic relationship)
        ('Vote Target', {
            'fields': ('content_type', 'object_id', 'get_voted_object'),
            'description': 'Generic relationship to the voted object'
        }),

        # Section 2: Vote Information
        ('Vote Information', {
            'fields': ('user', 'is_upvote', 'created_at'),
        }),
    )

    readonly_fields = [
        'created_at',
        'get_voted_object',
        'content_type',
        'object_id',
        'user'
    ]


    # Display the type of object being voted on.
    # This returns the model name (e.g., 'review', 'reviewcomment):
    def get_voted_object_type(self, obj):
        return obj.voted_object_type or 'Unknown'

    get_voted_object_type.short_description = 'Object Type'


    # Display a human-readable description of the voted object with a clickable link:
    def get_voted_object(self, obj):
        if obj.voted_object and obj.content_type:
            # Generate admin URL for the voted object
            url = reverse(
                f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                args=[obj.object_id]
            )
            return format_html('<a href="{}">{}</a>', url, obj.voted_object)

        return f"{obj.content_type.model if obj.content_type else 'Unknown'} #{obj.object_id} (deleted)"

    get_voted_object.short_description = 'Voted Object'



# ----------------------------------------------------------------------------- #
# Custom admin interface for the generic Report model.                          #
#                                                                               #
# The Report model uses Django's ContentTypes framework with GenericForeignKey  #
# to handle reports for ANY type of content in a truly generic way.             #
#                                                                               #
# This admin interface makes it easy for moderators to:                         #
# - View and filter reports by type, status, and content type                   #
# - See what object is being reported                                           #
# - Update report status and add review notes                                   #
# - Track who reported and who reviewed each report                             #
# ----------------------------------------------------------------------------- #
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'get_reported_object_type',   # Shows the model type (location, review, reviewcomment, etc.)
        'get_reported_object',        # Shows a human-readable description
        'report_type',                # Spam, Harassment, Duplicate, etc.
        'reported_by',                # Who submitted the report
        'status',                     # Pending, Reviewed, Resolved, Dismissed
        'created_at',                 # When the report was submitted
        'reviewed_by',                # Who reviewed it (if reviewed)
    ]

    list_filter = [
        'status',
        'report_type',
        'content_type',               # Filter by model type
        'created_at',
        'reviewed_at',
    ]

    search_fields = [
        'description',
        'reported_by__username',
        'reviewed_by__username',
        'review_notes',
        'object_id',
    ]

    ordering = ['-created_at']
    list_per_page = 50

    fieldsets = (
        # Section 1: What's being reported (generic relationship)
        ('Report Target', {
            'fields': ('content_type', 'object_id', 'get_reported_object'),
            'description': 'Generic relationship to the reported object'
        }),

        # Section 2: Report details
        ('Report Information', {
            'fields': ('report_type', 'description', 'reported_by', 'created_at', 'updated_at'),
        }),

        # Section 3: Additional data (JSON field)
        ('Additional Data', {
            'fields': ('additional_data',),
            'description': 'Extra context stored as JSON (e.g., duplicate location ID)',
            'classes': ('collapse',),
        }),

        # Section 4: Moderation tracking
        ('Moderation', {
            'fields': ('status', 'reviewed_by', 'review_notes', 'reviewed_at'),
        }),
    )

    readonly_fields = [
        'created_at',
        'updated_at',
        'reported_by',
        'content_type',
        'object_id',
        'get_reported_object',
        'report_type',
        'description',
        'additional_data'
    ]


    # Display the type of object being reported.
    # This returns the model name (e.g., 'location', 'review', 'reviewcomment'):
    def get_reported_object_type(self, obj):
        return obj.reported_object_type or 'Unknown'

    get_reported_object_type.short_description = 'Content Type'


    # Display a human-readable description of the reported object with a clickable link:
    def get_reported_object(self, obj):
        if obj.reported_object and obj.content_type:
            # Generate admin URL for the reported object
            url = reverse(
                f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                args=[obj.object_id]
            )
            return format_html('<a href="{}">{}</a>', url, obj.reported_object)

        return f"{obj.content_type.model if obj.content_type else 'Unknown'} #{obj.object_id} (deleted)"

    get_reported_object.short_description = 'Reported Object'



# ----------------------------------------------------------------------------- #
# Custom admin interface for EmailBounce model.                                 #
#                                                                               #
# Admin interface for viewing and managing email bounces with:                  #
# - Filter by bounce type, suppression status                                   #
# - Search by email address                                                     #
# - View detailed bounce information                                            #
# - Bulk actions for suppression management                                     #
# ----------------------------------------------------------------------------- #
class EmailBounceAdmin(admin.ModelAdmin):
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


    # Link to user admin page
    def user_link(self, obj):
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return '-'
    user_link.short_description = 'User'


    # Colored badge for bounce type
    def bounce_type_badge(self, obj):
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


    # Colored badge for suppression status
    def suppressed_badge(self, obj):
        if obj.suppressed:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">SUPPRESSED</span>'
            )
        return format_html(
            '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">ACTIVE</span>'
        )
    suppressed_badge.short_description = 'Status'


    # Display diagnostic code with formatting
    def diagnostic_code_display(self, obj):
        if obj.diagnostic_code:
            return format_html('<pre>{}</pre>', obj.diagnostic_code)
        return '-'
    diagnostic_code_display.short_description = 'Diagnostic Code'

    # Display raw notification JSON with formatting
    def raw_notification_display(self, obj):
        import json
        return format_html(
            '<pre>{}</pre>',
            json.dumps(obj.raw_notification, indent=2)
        )
    raw_notification_display.short_description = 'Raw SNS Notification'


    # Add bounced emails to suppression list
    def mark_as_suppressed(self, request, queryset):
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


    # Remove emails from suppression list
    def remove_from_suppression(self, request, queryset):
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



# ----------------------------------------------------------------------------- #
# Custom admin interface for EmailComplaint model.                              #
#                                                                               #
# Admin interface for viewing and managing email complaints with:               #
# - Filter by complaint type, review status                                     #
# - Search by email address                                                     #
# - View detailed complaint information                                         #
# - Mark complaints as reviewed                                                 #
# ----------------------------------------------------------------------------- #
class EmailComplaintAdmin(admin.ModelAdmin):
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


    # Link to user admin page
    def user_link(self, obj):
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return '-'
    user_link.short_description = 'User'


    # Colored badge for complaint type
    def complaint_type_badge(self, obj):
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            obj.complaint_type.upper()
        )
    complaint_type_badge.short_description = 'Type'


    # Badge for review status
    def reviewed_badge(self, obj):
        if obj.reviewed:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">REVIEWED</span>'
            )
        return format_html(
            '<span style="background-color: orange; color: white; padding: 3px 10px; border-radius: 3px;">PENDING</span>'
        )
    reviewed_badge.short_description = 'Review Status'


    # Badge for suppression status
    def suppressed_badge(self, obj):
        if obj.suppressed:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">SUPPRESSED</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">NOT SUPPRESSED</span>'
        )
    suppressed_badge.short_description = 'Status'


    # Display raw notification JSON with formatting
    def raw_notification_display(self, obj):
        import json
        return format_html(
            '<pre>{}</pre>',
            json.dumps(obj.raw_notification, indent=2)
        )
    raw_notification_display.short_description = 'Raw SNS Notification'


    # Mark complaints as reviewed
    def mark_as_reviewed(self, request, queryset):
        count = queryset.update(reviewed=True)
        self.message_user(request, f'{count} complaint(s) marked as reviewed.')
    mark_as_reviewed.short_description = 'Mark as reviewed'


    # Mark complaints as unreviewed
    def mark_as_unreviewed(self, request, queryset):
        count = queryset.update(reviewed=False)
        self.message_user(request, f'{count} complaint(s) marked as unreviewed.')
    mark_as_unreviewed.short_description = 'Mark as unreviewed'



# ----------------------------------------------------------------------------- #
# Custom admin interface for EmailSuppressionList model.                        #
#                                                                               #
# Admin interface for managing email suppression list with:                     #
# - Filter by reason, active status                                             #
# - Search by email address                                                     #
# - Bulk activate/deactivate suppressions                                       #
# - View linked bounce/complaint records                                        #
# ----------------------------------------------------------------------------- #
class EmailSuppressionListAdmin(admin.ModelAdmin):
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


    # Link to user admin page
    def user_link(self, obj):
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return '-'
    user_link.short_description = 'User'


    # Colored badge for suppression reason
    def reason_badge(self, obj):
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


    # Badge for active status
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">ACTIVE</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">INACTIVE</span>'
        )
    is_active_badge.short_description = 'Status'


    # Link to related bounce record
    def bounce_link(self, obj):
        if obj.bounce:
            return format_html(
                '<a href="/admin/starview_app/emailbounce/{}/change/">View Bounce #{}</a>',
                obj.bounce.id,
                obj.bounce.id
            )
        return '-'
    bounce_link.short_description = 'Related Bounce'


    # Link to related complaint record
    def complaint_link(self, obj):
        if obj.complaint:
            return format_html(
                '<a href="/admin/starview_app/emailcomplaint/{}/change/">View Complaint #{}</a>',
                obj.complaint.id,
                obj.complaint.id
            )
        return '-'
    complaint_link.short_description = 'Related Complaint'


    # Activate suppression for selected emails
    def activate_suppression(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} suppression(s) activated.')
    activate_suppression.short_description = 'Activate suppression'


    # Deactivate suppression for selected emails
    def deactivate_suppression(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} suppression(s) deactivated.')
    deactivate_suppression.short_description = 'Deactivate suppression'



# ----------------------------------------------------------------------------- #
# Custom admin interface for AuditLog model.                                    #
#                                                                               #
# Admin interface for viewing security audit logs with:                         #
# - Read-only access (audit logs are immutable)                                 #
# - Filter by event type, timestamp, success status                             #
# - Search by username and IP address                                           #
# - View metadata and user agent details                                        #
# ----------------------------------------------------------------------------- #
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'event_type_badge',
        'user_display',
        'ip_address',
        'success_badge',
    ]

    list_filter = [
        'event_type',
        'success',
        ('timestamp', admin.DateFieldListFilter),
    ]

    search_fields = [
        'username',
        'ip_address',
        'message',
        'user__username',
    ]

    readonly_fields = [
        'event_type',
        'timestamp',
        'success',
        'message',
        'user',
        'username',
        'ip_address',
        'user_agent',
        'metadata_display',
    ]

    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'timestamp', 'success', 'message')
        }),
        ('User Information', {
            'fields': ('user', 'username')
        }),
        ('Request Context', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Metadata', {
            'fields': ('metadata_display',),
            'classes': ('collapse',)
        }),
    )

    # Disable add and delete permissions (audit logs are append-only)
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # Badge for event type
    def event_type_badge(self, obj):
        colors = {
            'login_success': 'green',
            'login_failed': 'red',
            'login_locked': 'darkred',
            'logout': 'gray',
            'registration_success': 'green',
            'registration_failed': 'orange',
            'password_reset_requested': 'blue',
            'password_changed': 'blue',
            'permission_denied': 'red',
            'access_forbidden': 'red',
        }
        color = colors.get(obj.event_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_event_type_display()
        )
    event_type_badge.short_description = 'Event Type'

    # Display username or user
    def user_display(self, obj):
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return obj.username or 'anonymous'
    user_display.short_description = 'User'

    # Badge for success status
    def success_badge(self, obj):
        if obj.success:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">SUCCESS</span>'
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">FAILED</span>'
        )
    success_badge.short_description = 'Status'

    # Display metadata JSON with formatting
    def metadata_display(self, obj):
        import json
        if obj.metadata:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.metadata, indent=2)
            )
        return '-'
    metadata_display.short_description = 'Metadata'



# ----------------------------------------------------------------------------- #
# Custom admin interface for Follow model.                                      #
#                                                                               #
# Admin interface for viewing and managing user follow relationships with:      #
# - Filter by creation date                                                     #
# - Search by follower or following username                                    #
# - View follower/following relationships                                       #
# - Bulk delete actions                                                         #
# ----------------------------------------------------------------------------- #
class FollowAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'follower_link',
        'arrow',
        'following_link',
        'created_at',
    ]

    list_filter = [
        ('created_at', admin.DateFieldListFilter),
    ]

    search_fields = [
        'follower__username',
        'following__username',
    ]

    readonly_fields = [
        'follower',
        'following',
        'created_at',
    ]

    fieldsets = (
        ('Follow Relationship', {
            'fields': ('follower', 'following', 'created_at'),
            'description': 'User follow relationship'
        }),
    )

    ordering = ['-created_at']
    list_per_page = 50

    # Disable add permission (users create follows through the app)
    def has_add_permission(self, request):
        return False

    # Link to follower user admin page
    def follower_link(self, obj):
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.follower.id,
            obj.follower.username
        )
    follower_link.short_description = 'Follower'

    # Arrow symbol between follower and following
    def arrow(self, obj):
        return '→'
    arrow.short_description = ''

    # Link to following user admin page
    def following_link(self, obj):
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.following.id,
            obj.following.username
        )
    following_link.short_description = 'Following'


# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                          ADMIN SITE REGISTERS                                         #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# Register models with basic admin interface
admin.site.register(Location)
admin.site.register(UserProfile)
admin.site.register(FavoriteLocation)
admin.site.register(Review)
admin.site.register(ReviewComment)
admin.site.register(ReviewPhoto)

# Register Follow model with custom admin interface
admin.site.register(Follow, FollowAdmin)

# Register generic models with custom admin interfaces
admin.site.register(Vote, VoteAdmin)
admin.site.register(Report, ReportAdmin)

# Register email event models with custom admin interfaces
admin.site.register(EmailBounce, EmailBounceAdmin)
admin.site.register(EmailComplaint, EmailComplaintAdmin)
admin.site.register(EmailSuppressionList, EmailSuppressionListAdmin)

# Register audit log model with custom admin interface (read-only)
admin.site.register(AuditLog, AuditLogAdmin)
