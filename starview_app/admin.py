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
from .models import UserProfile, FavoriteLocation, Location
from .models import Review, ReviewComment, ReviewPhoto, Report, Vote



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

# Register generic models with custom admin interfaces
admin.site.register(Vote, VoteAdmin)
admin.site.register(Report, ReportAdmin)
