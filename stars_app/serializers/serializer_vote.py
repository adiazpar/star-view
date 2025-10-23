# ----------------------------------------------------------------------------------------------------- #
# This serializer_vote.py file defines the serializer for the Vote model:                               #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST Framework serializer for transforming Vote models between Python objects and JSON.      #
# The Vote model uses Django's ContentTypes framework to enable voting (upvote/downvote) on ANY         #
# content type in the project (reviews, comments, locations, etc.) without modification.                #
#                                                                                                       #
# Key Features:                                                                                         #
# - VoteSerializer: Generic serializer that works with any votable content type                         #
# - ContentTypes integration: Uses content_type + object_id to reference any Django model               #
# - User context: Tracks which user cast each vote                                                      #
# - Human-readable helpers: Provides string representation of voted objects                             #
# - Completely generic: No changes needed to support new votable models                                 #
#                                                                                                       #
# Architecture:                                                                                         #
# This serializer leverages Django's ContentTypes framework for maximum flexibility. To add voting      #
# to a new model, just add a GenericRelation('Vote') field - no serializer changes required.            #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from rest_framework import serializers
from ..models import Vote



# ----------------------------------------------------------------------------- #
# Generic serializer for the Vote model.                                        #
#                                                                               #
# Uses Django's ContentTypes framework to handle votes for ANY model in the     #
# project. The voted object is specified via content_type + object_id.          #
# ----------------------------------------------------------------------------- #
class VoteSerializer(serializers.ModelSerializer):

    # User information:
    user = serializers.ReadOnlyField(
        source='user.username',
        help_text="Username of the person who cast this vote"
    )

    # Content type information:
    voted_object_type = serializers.ReadOnlyField(
        help_text="Type of object being voted on (e.g., 'locationreview', 'reviewcomment')"
    )

    voted_object_str = serializers.SerializerMethodField(
        help_text="String representation of the voted object"
    )


    class Meta:
        model = Vote

        fields = [
            # Basic vote info
            'id',
            'created_at',

            # Generic relationship fields
            'content_type',
            'object_id',
            'voted_object_type',  # Helper field showing model name
            'voted_object_str',   # Human-readable string of the object

            # Vote data
            'user',
            'is_upvote',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'user',
            'content_type',  # Auto-set from the object being voted on
        ]


    # ----------------------------------------------------------------------------- #
    # Returns a human-readable string representation of the voted object.           #
    #                                                                               #
    # This calls the __str__ method on the voted object to get a meaningful         #
    # description.                                                                  #
    # ----------------------------------------------------------------------------- #
    def get_voted_object_str(self, obj):
        if obj.voted_object:
            return str(obj.voted_object)
        return f"{obj.content_type.model if obj.content_type else 'Unknown'} #{obj.object_id}"
