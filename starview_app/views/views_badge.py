# ----------------------------------------------------------------------------------------------------- #
# This views_badge.py file handles badge-related API endpoints:                                         #
#                                                                                                       #
# Purpose:                                                                                              #
# Manages user badge achievements and display. Enables users to view earned/in-progress/locked badges   #
# and pin their favorite badges to their profile header.                                                #
#                                                                                                       #
# Key Features:                                                                                         #
# - Get user's badge collection (earned, in-progress, locked)                                           #
# - Pin/unpin badges (max 3 pinned badges)                                                              #
# - Badge progress calculated on-demand (not stored)                                                    #
# - Public endpoint (anyone can view badges)                                                            #
# - Only owners can modify pinned badges                                                                #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

# DRF imports:
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, exceptions
from rest_framework.response import Response

# Model imports:
from ..models import Badge, UserBadge, UserProfile

# Service imports:
from starview_app.services.badge_service import BadgeService



# ----------------------------------------------------------------------------- #
# Get user's PUBLIC badge display (for profile pages).                          #
#                                                                               #
# Returns ONLY earned badges - used for public profile display.                 #
# This endpoint shows the same data regardless of who is viewing.               #
#                                                                               #
# HTTP Method: GET                                                              #
# Endpoint: /api/users/{username}/badges/                                       #
# Authentication: Not required (public)                                         #
# Returns: {earned: [...], pinned_badge_ids: [...]}                             #
# ----------------------------------------------------------------------------- #
@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_badges(request, username):
    user = get_object_or_404(User, username=username)

    # Get badge progress from service
    badge_data = BadgeService.get_user_badge_progress(user)

    # Get pinned badge IDs from user profile
    try:
        profile = user.userprofile
        pinned_badge_ids = profile.pinned_badge_ids or []
    except UserProfile.DoesNotExist:
        pinned_badge_ids = []

    # Serialize earned badges only (public display)
    earned_badges = []
    for item in badge_data['earned']:
        badge = item['badge']
        earned_badges.append({
            'badge_id': badge.id,
            'name': badge.name,
            'slug': badge.slug,
            'description': badge.description,
            'category': badge.category,
            'tier': badge.tier,
            'is_rare': badge.is_rare,
            'icon_path': badge.icon_path,
            'earned_at': item['earned_at'].isoformat(),
        })

    return Response({
        'earned': earned_badges,
        'pinned_badge_ids': pinned_badge_ids,
    }, status=status.HTTP_200_OK)


# ----------------------------------------------------------------------------- #
# Get user's FULL badge collection (for private badge collection page).         #
#                                                                               #
# Returns ALL badges: earned, in-progress, and locked.                          #
# Only accessible by the authenticated user for their own profile.              #
#                                                                               #
# HTTP Method: GET                                                              #
# Endpoint: /api/users/me/badges/collection/                                    #
# Authentication: Required                                                      #
# Returns: {earned: [...], in_progress: [...], locked: [...],                   #
#           pinned_badge_ids: [...]}                                             #
# ----------------------------------------------------------------------------- #
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_badge_collection(request):
    user = request.user

    # Get badge progress from service
    badge_data = BadgeService.get_user_badge_progress(user)

    # Serialize earned badges
    earned_badges = []
    for item in badge_data['earned']:
        badge = item['badge']
        earned_badges.append({
            'badge_id': badge.id,
            'name': badge.name,
            'slug': badge.slug,
            'description': badge.description,
            'category': badge.category,
            'tier': badge.tier,
            'is_rare': badge.is_rare,
            'icon_path': badge.icon_path,
            'earned_at': item['earned_at'].isoformat(),
        })

    # Serialize in-progress badges
    in_progress_badges = []
    for item in badge_data['in_progress']:
        badge = item['badge']
        in_progress_badges.append({
            'badge_id': badge.id,
            'name': badge.name,
            'slug': badge.slug,
            'description': badge.description,
            'category': badge.category,
            'tier': badge.tier,
            'is_rare': badge.is_rare,
            'icon_path': badge.icon_path,
            'current_progress': item['current_progress'],
            'criteria_value': item['criteria_value'],
            'percentage': item['percentage'],
        })

    # Serialize locked badges
    locked_badges = []
    for item in badge_data['locked']:
        badge = item['badge']
        locked_badges.append({
            'badge_id': badge.id,
            'name': badge.name,
            'slug': badge.slug,
            'description': badge.description,
            'category': badge.category,
            'tier': badge.tier,
            'is_rare': badge.is_rare,
            'icon_path': badge.icon_path,
            'criteria_value': badge.criteria_value,
        })

    # Get user's pinned badge IDs from profile
    try:
        user_profile = user.userprofile
        pinned_badge_ids = user_profile.pinned_badge_ids or []
    except:
        pinned_badge_ids = []

    return Response({
        'earned': earned_badges,
        'in_progress': in_progress_badges,
        'locked': locked_badges,
        'pinned_badge_ids': pinned_badge_ids,
    }, status=status.HTTP_200_OK)


# ----------------------------------------------------------------------------- #
# Update user's pinned badges.                                                  #
#                                                                               #
# Allows users to pin up to 3 badges to their profile header.                   #
# Only works for badges the user has earned.                                    #
#                                                                               #
# HTTP Method: PATCH                                                            #
# Endpoint: /api/users/me/badges/pin/                                           #
# Authentication: Required (only for own profile)                               #
# Body: {"pinned_badge_ids": [1, 3, 7]}                                         #
# Returns: Updated pinned badges list                                           #
# ----------------------------------------------------------------------------- #
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_pinned_badges(request):
    pinned_badge_ids = request.data.get('pinned_badge_ids', [])

    # Validation: Max 3 badges
    if len(pinned_badge_ids) > 3:
        raise exceptions.ValidationError('You can only pin up to 3 badges.')

    # Validation: Must be a list of integers
    if not isinstance(pinned_badge_ids, list):
        raise exceptions.ValidationError('pinned_badge_ids must be a list.')

    if not all(isinstance(id, int) for id in pinned_badge_ids):
        raise exceptions.ValidationError('All badge IDs must be integers.')

    # Validation: Can only pin badges you've earned
    if pinned_badge_ids:
        earned_badge_ids = set(
            UserBadge.objects.filter(user=request.user).values_list('badge_id', flat=True)
        )
        for badge_id in pinned_badge_ids:
            if badge_id not in earned_badge_ids:
                raise exceptions.ValidationError(f'You have not earned badge ID {badge_id}.')

    # Update user profile
    profile = request.user.userprofile
    profile.pinned_badge_ids = pinned_badge_ids
    profile.save(update_fields=['pinned_badge_ids'])

    # Get badge details for response
    if pinned_badge_ids:
        pinned_badges = Badge.objects.filter(id__in=pinned_badge_ids)
        pinned_badges_data = [{
            'badge_id': badge.id,
            'name': badge.name,
            'slug': badge.slug,
            'icon_path': badge.icon_path,
        } for badge in pinned_badges]
    else:
        pinned_badges_data = []

    return Response({
        'detail': 'Pinned badges updated successfully.',
        'pinned_badge_ids': pinned_badge_ids,
        'pinned_badges': pinned_badges_data,
    }, status=status.HTTP_200_OK)
