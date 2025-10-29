# ----------------------------------------------------------------------------------------------------- #
# This vote_service.py file handles vote toggle operations for reviews and comments:                    #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides centralized business logic for upvoting/downvoting content using Django's ContentTypes       #
# framework. Eliminates code duplication between ReviewViewSet and CommentViewSet.                      #
#                                                                                                       #
# Key Features:                                                                                         #
# - Toggle Logic: Same vote removes it, different vote changes it                                       #
# - Generic Support: Works with any content type via ContentTypes framework                             #
# - Aggregate Calculation: Returns updated vote counts in a single operation                            #
# - Business Rules: Centralizes vote validation and toggle behavior                                     #
#                                                                                                       #
# Service Layer Pattern:                                                                                #
# This service separates business logic from views, following Django best practices:                    #
# - Models define data structure (Vote model)                                                           #
# - Services define business logic (vote toggle operations)                                             #
# - Views coordinate between user requests and services                                                 #
#                                                                                                       #
# Usage:                                                                                                #
# - All methods are static and can be called independently                                              #
# - Used by ReviewViewSet and CommentViewSet for consistent vote handling                               #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.contrib.contenttypes.models import ContentType
from starview_app.models.model_vote import Vote


class VoteService:

    # ----------------------------------------------------------------------------- #
    # Handle a vote request with full validation (primary method for views).        #
    #                                                                               #
    # Performs all necessary validations before processing the vote:                #
    # 1. Validates vote_type parameter                                              #
    # 2. Prevents users from voting on their own content                            #
    # 3. Calls toggle_vote() to process the vote                                    #
    #                                                                               #
    # Args:     user (User): The user casting the vote                              #
    #           content_object: The object being voted on (Review, ReviewComment)   #
    #           vote_type (str): 'up' for upvote, 'down' for downvote               #
    # Returns:  dict: vote_data (upvotes, downvotes, vote_count, user_vote)         #
    # Raises:   ValidationError: If validation fails                                #
    # ----------------------------------------------------------------------------- #
    @staticmethod
    def handle_vote_request(user, content_object, vote_type):
        from rest_framework.exceptions import ValidationError

        # Validate vote type
        if vote_type not in ['up', 'down']:
            raise ValidationError('Vote type must be "up" or "down"')

        # Prevent users from voting on their own content
        if hasattr(content_object, 'user') and content_object.user == user:
            raise ValidationError('You cannot vote on your own content')

        # Process the vote
        is_upvote = vote_type == 'up'
        vote_data = VoteService.toggle_vote(user, content_object, is_upvote)

        return vote_data


    # ----------------------------------------------------------------------------- #
    # Toggle a user's vote on any content object (review, comment, etc.).           #
    #                                                                               #
    # Vote Toggle Logic:                                                            #
    # - No existing vote → Create new vote                                          #
    # - Same vote type → Remove vote (toggle off)                                   #
    # - Different vote type → Change vote                                           #
    #                                                                               #
    # Args:     user (User): The user casting the vote                              #
    #           content_object: The object being voted on (Review, ReviewComment)   #
    #           is_upvote (bool): True for upvote, False for downvote               #
    # Returns:  dict: vote_data (upvotes, downvotes, vote_count, user_vote)         #
    # ----------------------------------------------------------------------------- #
    @staticmethod
    def toggle_vote(user, content_object, is_upvote):
        # Get the ContentType for the content object
        content_type = ContentType.objects.get_for_model(content_object)

        # Get or create the vote
        vote, created = Vote.objects.get_or_create(
            user=user,
            content_type=content_type,
            object_id=content_object.id,
            defaults={'is_upvote': is_upvote}
        )

        user_vote = None
        if not created:
            # Vote already exists
            if vote.is_upvote == is_upvote:
                # Same vote type - remove the vote (toggle off)
                vote.delete()
                user_vote = None
            else:
                # Different vote type - update the vote
                vote.is_upvote = is_upvote
                vote.save()
                user_vote = 'up' if is_upvote else 'down'
        else:
            # New vote created
            user_vote = 'up' if is_upvote else 'down'

        # Calculate updated vote counts
        upvotes = Vote.objects.filter(
            content_type=content_type,
            object_id=content_object.id,
            is_upvote=True
        ).count()

        downvotes = Vote.objects.filter(
            content_type=content_type,
            object_id=content_object.id,
            is_upvote=False
        ).count()

        vote_count = upvotes - downvotes

        # Return vote data
        return {
            'upvotes': upvotes,
            'downvotes': downvotes,
            'vote_count': vote_count,
            'user_vote': user_vote
        }


    # ----------------------------------------------------------------------------- #
    # Get current vote counts for any content object without modifying votes.       #
    #                                                                               #
    # Useful for displaying vote information without performing a vote action.      #
    #                                                                               #
    # Args:     content_object: The object to get vote counts for                   #
    #           user (User): Optional user to check their vote status               #
    # Returns:  dict: Contains upvotes, downvotes, vote_count, user_vote            #
    # ----------------------------------------------------------------------------- #
    @staticmethod
    def get_vote_counts(content_object, user=None):
        try:
            content_type = ContentType.objects.get_for_model(content_object)

            upvotes = Vote.objects.filter(
                content_type=content_type,
                object_id=content_object.id,
                is_upvote=True
            ).count()

            downvotes = Vote.objects.filter(
                content_type=content_type,
                object_id=content_object.id,
                is_upvote=False
            ).count()

            vote_count = upvotes - downvotes

            # Check user's vote if user provided
            user_vote = None
            if user and user.is_authenticated:
                vote = Vote.objects.filter(
                    content_type=content_type,
                    object_id=content_object.id,
                    user=user
                ).first()

                if vote:
                    user_vote = 'up' if vote.is_upvote else 'down'

            return {
                'upvotes': upvotes,
                'downvotes': downvotes,
                'vote_count': vote_count,
                'user_vote': user_vote
            }

        except Exception as e:
            return {
                'upvotes': 0,
                'downvotes': 0,
                'vote_count': 0,
                'user_vote': None,
                'error': str(e)
            }
