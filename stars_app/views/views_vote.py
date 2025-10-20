# ----------------------------------------------------------------------------------------------------- #
# This views_vote.py file handles vote-related views and API endpoints:                                #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST API endpoints for managing votes on reviews and comments. Uses Django's ContentTypes   #
# framework to enable a single unified voting system across all votable content types.                 #
#                                                                                                       #
# Key Features:                                                                                         #
# - VoteViewSet: API for managing user votes (upvotes/downvotes)                                       #
# - Generic voting: Works with any content type via ContentTypes framework                             #
# - User-specific access: Users can only view and manage their own votes                               #
#                                                                                                       #
# Architecture:                                                                                         #
# - Uses Django REST Framework ViewSets for API endpoints                                              #
# - Integrates with ContentTypes framework for generic relationships                                   #
# - Replaces old separate ReviewVote and CommentVote models with unified Vote model                    #
# ----------------------------------------------------------------------------------------------------- #

# REST Framework imports:
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Model imports:
from stars_app.models.model_vote import Vote

# Serializer imports:
from stars_app.serializers import VoteSerializer



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                         VOTE VIEWSET                                                  #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

class VoteViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing votes using the generic Vote model.

    This replaces the old ReviewVoteViewSet and CommentVoteViewSet with a
    unified voting system that works across all votable content types.

    The Vote model uses Django's ContentTypes framework to handle votes
    on reviews, comments, and any other votable content.
    """
    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return all votes by the current user."""
        return Vote.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create a vote for the current user."""
        serializer.save(user=self.request.user)
