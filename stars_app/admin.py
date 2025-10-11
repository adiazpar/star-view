from django.contrib import admin

from stars_app.models.userprofile import UserProfile
from stars_app.models.favoritelocation import FavoriteLocation
from stars_app.models.viewinglocation import ViewingLocation
from stars_app.models.locationreview import LocationReview
from stars_app.models.reviewvote import ReviewVote
from stars_app.models.reviewcomment import ReviewComment
from stars_app.models.commentvote import CommentVote
from stars_app.models.reviewphoto import ReviewPhoto
from stars_app.models.reviewreport import ReviewReport
from stars_app.models.commentreport import CommentReport

# Register your models here.
admin.site.register(ViewingLocation)
admin.site.register(UserProfile)
admin.site.register(FavoriteLocation)
admin.site.register(LocationReview)
admin.site.register(ReviewVote)
admin.site.register(ReviewComment)
admin.site.register(CommentVote)

# Custom admin for ReviewPhoto with better display
class ReviewPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'review', 'caption', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['review__user__username', 'caption']
    ordering = ['-created_at']
    readonly_fields = ['thumbnail', 'created_at', 'updated_at']

admin.site.register(ReviewPhoto, ReviewPhotoAdmin)

# Custom admin for ReviewReport with better display
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'review', 'reported_by', 'report_type', 'status', 'created_at']
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = ['review__user__username', 'reported_by__username', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('review', 'reported_by', 'reviewed_by')

# Custom admin for CommentReport with better display  
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'comment', 'reported_by', 'report_type', 'status', 'created_at']
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = ['comment__user__username', 'reported_by__username', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('comment', 'reported_by', 'reviewed_by')

admin.site.register(ReviewReport, ReviewReportAdmin)
admin.site.register(CommentReport, CommentReportAdmin)
