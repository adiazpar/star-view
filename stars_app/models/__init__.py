from .model_viewing_location import ViewingLocation
from .model_user_profile import UserProfile
from .model_location_review import LocationReview
from .model_review_comment import ReviewComment
from .model_favorite_location import FavoriteLocation
from .model_review_photo import ReviewPhoto

# Unified report model (replaces LocationReport, ReviewReport, CommentReport)
from .model_report import Report

# Unified vote model (replaces ReviewVote, CommentVote)
from .model_vote import Vote

# Import signals to ensure they're registered
from stars_app import signals