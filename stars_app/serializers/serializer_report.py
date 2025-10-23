# ----------------------------------------------------------------------------------------------------- #
# This serializer_report.py file defines the serializer for the Report model:                           #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST Framework serializer for transforming Report models between Python objects and JSON.    #
# The Report model uses Django's ContentTypes framework to enable reporting of inappropriate content    #
# for ANY content type in the project (reviews, comments, locations, etc.) without modification.        #
#                                                                                                       #
# Key Features:                                                                                         #
# - ReportSerializer: Generic serializer that works with any reportable content type                    #
# - ContentTypes integration: Uses content_type + object_id to reference any Django model               #
# - Moderation support: Includes status tracking, review notes, and moderator assignment                #
# - User context: Tracks reporter and reviewing moderator                                               #
# - Human-readable helpers: Provides string representation of reported objects                          #
# - Additional data: JSON field for extra context (e.g., duplicate location ID)                         #
#                                                                                                       #
# Architecture:                                                                                         #
# This serializer leverages Django's ContentTypes framework for maximum flexibility. To add reporting   #
# to a new model, just add a GenericRelation('Report') field - no serializer changes required.          #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from rest_framework import serializers
from stars_app.models.model_report import Report



# ----------------------------------------------------------------------------- #
# Generic serializer for the Report model.                                      #
#                                                                               #
# Uses Django's ContentTypes framework to handle reports for ANY model in the   #
# project. The reported object is specified via content_type + object_id.       #
# ----------------------------------------------------------------------------- #
class ReportSerializer(serializers.ModelSerializer):

    # User information:
    reported_by = serializers.ReadOnlyField(
        source='reported_by.username',
        help_text="Username of the person who submitted this report"
    )

    reviewed_by = serializers.ReadOnlyField(
        source='reviewed_by.username',
        help_text="Username of the moderator who reviewed this report (if reviewed)"
    )

    # Content type information:
    reported_object_type = serializers.ReadOnlyField(
        help_text="Type of object being reported (e.g., 'viewinglocation', 'locationreview')"
    )

    reported_object_str = serializers.SerializerMethodField(
        help_text="String representation of the reported object"
    )


    class Meta:
        model = Report

        fields = [
            # Basic report info
            'id',
            'created_at',
            'updated_at',

            # Generic relationship fields
            'content_type',
            'object_id',
            'reported_object_type',  # Helper field showing model name
            'reported_object_str',   # Human-readable string of the object

            # Report details
            'reported_by',
            'report_type',
            'description',
            'status',

            # Additional data (JSON field for any extra context)
            'additional_data',

            # Moderation fields
            'reviewed_by',
            'review_notes',
            'reviewed_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'reported_by',
            'reviewed_by',
            'reviewed_at',
            'status',
            'content_type',  # Auto-set from the object being reported
        ]


    # ----------------------------------------------------------------------------- #
    # Returns a human-readable string representation of the reported object.        #
    #                                                                               #
    # This calls the __str__ method on the reported object to get a meaningful      #
    # description.                                                                  #
    # ----------------------------------------------------------------------------- #
    def get_reported_object_str(self, obj):
        if obj.reported_object:
            return str(obj.reported_object)
        return f"{obj.content_type.model if obj.content_type else 'Unknown'} #{obj.object_id}"
