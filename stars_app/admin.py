from django.contrib import admin

from stars_app.models.model_user_profile import UserProfile
from stars_app.models.model_favorite_location import FavoriteLocation
from stars_app.models.model_viewing_location import ViewingLocation
from stars_app.models.model_location_review import LocationReview
from stars_app.models.model_review_vote import ReviewVote
from stars_app.models.model_review_comment import ReviewComment
from stars_app.models.model_comment_vote import CommentVote
from stars_app.models.model_review_photo import ReviewPhoto

# Import the unified Report model (replaces LocationReport, ReviewReport, CommentReport)
from stars_app.models.model_report import Report


# ==================== CUSTOM ADMIN FOR GENERIC REPORT MODEL ====================

class ReportAdmin(admin.ModelAdmin):
    """
    Custom admin interface for the generic Report model.

    The Report model uses Django's ContentTypes framework with GenericForeignKey
    to handle reports for ANY type of content in a truly generic way.

    This admin interface makes it easy for moderators to:
    - View and filter reports by type, status, and content type
    - See what object is being reported
    - Update report status and add review notes
    - Track who reported and who reviewed each report
    """

    # ========== LIST VIEW CONFIGURATION ==========

    list_display = [
        'id',
        'get_reported_object_type',   # Shows the model type (viewinglocation, locationreview, etc.)
        'get_reported_object_str',    # Shows a human-readable description
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

    # ========== DETAIL VIEW CONFIGURATION ==========

    fieldsets = (
        # Section 1: What's being reported (generic relationship)
        ('Report Target', {
            'fields': ('content_type', 'object_id', 'get_reported_object_display'),
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
        'get_reported_object_display'
    ]

    # ========== CUSTOM METHODS ==========

    def get_reported_object_type(self, obj):
        """
        Display the type of object being reported.
        Returns the model name (e.g., 'viewinglocation', 'locationreview')
        """
        return obj.reported_object_type or 'Unknown'

    get_reported_object_type.short_description = 'Content Type'

    def get_reported_object_str(self, obj):
        """
        Display a human-readable description of what's being reported.
        """
        if obj.reported_object:
            return str(obj.reported_object)
        return f"{obj.content_type.model if obj.content_type else 'Unknown'} #{obj.object_id}"

    get_reported_object_str.short_description = 'Reported Object'

    def get_reported_object_display(self, obj):
        """
        Display the reported object in the detail view with a link to it.
        """
        if obj.reported_object:
            return f"{obj.content_type.model}: {obj.reported_object}"
        return f"{obj.content_type.model if obj.content_type else 'Unknown'} #{obj.object_id} (deleted)"

    get_reported_object_display.short_description = 'Reported Object'


# ==================== MODEL REGISTRATIONS ====================

# Register models with basic admin interface
admin.site.register(ViewingLocation)
admin.site.register(UserProfile)
admin.site.register(FavoriteLocation)
admin.site.register(LocationReview)
admin.site.register(ReviewVote)
admin.site.register(ReviewComment)
admin.site.register(CommentVote)
admin.site.register(ReviewPhoto)

# Register the unified Report model with custom admin interface
admin.site.register(Report, ReportAdmin)
