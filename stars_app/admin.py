from django.contrib import admin

from stars_app.models.model_user_profile import UserProfile
from stars_app.models.model_favorite_location import FavoriteLocation
from stars_app.models.model_viewing_location import ViewingLocation
from stars_app.models.model_location_review import LocationReview
from stars_app.models.model_review_vote import ReviewVote
from stars_app.models.model_review_comment import ReviewComment
from stars_app.models.model_comment_vote import CommentVote
from stars_app.models.model_review_photo import ReviewPhoto
from stars_app.models.model_review_report import ReviewReport
from stars_app.models.model_comment_report import CommentReport

# Register your models here.
admin.site.register(ViewingLocation)
admin.site.register(UserProfile)
admin.site.register(FavoriteLocation)
admin.site.register(LocationReview)
admin.site.register(ReviewVote)
admin.site.register(ReviewComment)
admin.site.register(CommentVote)
admin.site.register(ReviewPhoto)
admin.site.register(ReviewReport)
admin.site.register(CommentReport)
