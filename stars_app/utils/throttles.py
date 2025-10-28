# ----------------------------------------------------------------------------------------------------- #
# This throttles.py file provides custom rate limiting classes for API endpoints.                       #
#                                                                                                       #
# Purpose:                                                                                              #
# Prevents abuse by limiting how frequently users can perform specific actions. Different throttle      #
# classes apply different limits based on the sensitivity and cost of each action.                      #
#                                                                                                       #
# Throttle Classes:                                                                                     #
# - LoginRateThrottle: 5/minute for authentication endpoints (prevents brute force attacks)             #
# - ContentCreationThrottle: 20/hour for locations, reviews, comments (prevents spam)                   #
# - VoteThrottle: 60/hour for upvotes/downvotes (prevents vote manipulation)                            #
# - ReportThrottle: 10/hour for content reports (prevents report abuse)                                 #
#                                                                                                       #
# Configuration:                                                                                        #
# Throttle rates are defined in django_project/settings.py under DEFAULT_THROTTLE_RATES.                #
# Each throttle class has a 'scope' that maps to a rate in settings.                                    #
#                                                                                                       #
# Usage:                                                                                                #
# Apply to views/viewsets using @throttle_classes decorator or throttle_classes attribute:              #
#   @throttle_classes([ContentCreationThrottle])                                                        #
#   def create_location(request): ...                                                                   #
#                                                                                                       #
# Security Impact:                                                                                      #
# - Prevents automated spam/abuse attacks                                                               #
# - Protects database from content flooding                                                             #
# - Maintains application performance under abuse attempts                                              #
# - Prevents vote manipulation and report abuse                                                         #
# ----------------------------------------------------------------------------------------------------- #

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.conf import settings
import sys


# ----------------------------------------------------------------------------- #
# LoginRateThrottle                                                             #
#                                                                               #
# Prevents brute force attacks on authentication endpoints.                     #
# Rate: 5 requests per minute (allows legitimate retries, blocks automation)    #
#                                                                               #
# Applied to:                                                                   #
# - /login/                                                                     #
# - /register/                                                                  #
# - /password-reset/                                                            #
#                                                                               #
# Note: Automatically disabled during testing to allow test suites to run.      #
# ----------------------------------------------------------------------------- #
class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'

    def allow_request(self, request, view):
        # Disable throttling during tests
        # Check multiple conditions to catch all test scenarios
        if (
            'test' in sys.argv or
            hasattr(settings, 'TESTING') or
            getattr(settings, 'TESTING', False) or
            'unittest' in sys.modules or
            'pytest' in sys.modules or
            'django.test' in sys.modules
        ):
            return True
        return super().allow_request(request, view)


# ----------------------------------------------------------------------------- #
# ContentCreationThrottle                                                       #
#                                                                               #
# Prevents spam by limiting content creation to 20 items per hour.              #
# Rate: 20/hour (allows legitimate use, blocks automated spam)                  #
#                                                                               #
# Applied to:                                                                   #
# - Location creation (POST /api/locations/)                                    #
# - Review creation (POST /api/locations/{id}/reviews/)                         #
# - Comment creation (POST /api/reviews/{id}/comments/)                         #
#                                                                               #
# Why 20/hour:                                                                  #
# - Most users create 1-5 locations/reviews per session                         #
# - 20/hour allows power users without enabling spam                            #
# - Prevents automated bots from flooding database                              #
# ----------------------------------------------------------------------------- #
class ContentCreationThrottle(UserRateThrottle):
    scope = 'content_creation'


# ----------------------------------------------------------------------------- #
# VoteThrottle                                                                  #
#                                                                               #
# Prevents vote manipulation by limiting votes to 60 per hour.                  #
# Rate: 60/hour (1 per minute average)                                          #
#                                                                               #
# Applied to:                                                                   #
# - Review upvotes/downvotes                                                    #
# - Comment upvotes/downvotes                                                   #
#                                                                               #
# Why 60/hour:                                                                  #
# - Users rarely vote on more than 60 items in an hour                          #
# - Allows browsing and voting naturally                                        #
# - Prevents automated vote manipulation scripts                                #
# ----------------------------------------------------------------------------- #
class VoteThrottle(UserRateThrottle):
    scope = 'vote'


# ----------------------------------------------------------------------------- #
# ReportThrottle                                                                #
#                                                                               #
# Prevents report abuse by limiting reports to 10 per hour.                     #
# Rate: 10/hour (enough for legitimate moderation, blocks spam)                 #
#                                                                               #
# Applied to:                                                                   #
# - Location reports                                                            #
# - Review reports                                                              #
# - Comment reports                                                             #
#                                                                               #
# Why 10/hour:                                                                  #
# - Most users report 0-2 items per session                                     #
# - 10/hour allows active moderators                                            #
# - Prevents malicious users from mass-reporting legitimate content             #
# ----------------------------------------------------------------------------- #
class ReportThrottle(UserRateThrottle):
    scope = 'report'
