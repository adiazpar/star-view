# ----------------------------------------------------------------------------------------------------- #
# This response_service.py file provides centralized response handling for all API endpoints:           #
#                                                                                                       #
# Purpose:                                                                                              #
# Standardizes all API responses across the application using Django REST Framework, ensuring           #
# consistent JSON structure for both success and error cases.                                           #
#                                                                                                       #
# Key Features:                                                                                         #
# - DRF-native responses: Uses DRF Response objects following REST API best practices                   #
# - Automatic logging: Built-in logging for all responses (info for success, error for failures)        #
# - Flexible data inclusion: Optional data payloads for complex responses                               #
# - Standardized error handling: Consistent error format across all endpoints                           #
#                                                                                                       #
# Standard Response Format:                                                                             #
# Success: {'detail': '...', ...data}                                                                   #
# Error:   {'detail': '...', 'errors': {...}}                                                           #
#                                                                                                       #
# DRF Convention:                                                                                       #
# The 'detail' key is the DRF standard for message responses, which integrates seamlessly with          #
# DRF's browsable API, exception handling, and serializer validation errors.                            #
#                                                                                                       #
# Usage:                                                                                                #
# - All endpoints: Use success() and error() methods (returns DRF Response)                             #
# - All responses are automatically logged with appropriate severity levels                             #
# - Use with DRF APIViews, ViewSets, or @api_view decorators                                            #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
import logging
from rest_framework.response import Response
from rest_framework import status

# Configure logger:
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------- #
# Centralized response handling service for DRF API endpoints.                  #
#                                                                               #
# Provides standardized DRF Response structures with built-in logging           #
# following Django REST Framework conventions.                                  #
# ----------------------------------------------------------------------------- #
class ResponseService:
    
    # ----------------------------------------------------------------------------- #
    # Return a standardized success response for DRF API endpoints.                 #
    #                                                                               #
    # Creates a DRF Response with 'detail' key (DRF convention) and logs the        #
    # success event. Used for all API endpoints across the application.             #
    #                                                                               #
    # Args:     message (str): Success message to display to user                   #
    #           data (dict): Optional additional data to include in response        #
    #           status_code (int): HTTP status code (default: 200)                  #
    #           log_extra (dict): Optional extra context for logging                #
    # Returns:  Response: DRF Response object                                       #
    # ----------------------------------------------------------------------------- #
    @staticmethod
    def success(message, data=None, status_code=status.HTTP_200_OK, log_extra=None):
        response = {'detail': message}
        if data:
            response.update(data)

        # Log the success event
        log_message = f"Success response: {message}"
        if log_extra:
            logger.info(log_message, extra=log_extra)
        else:
            logger.info(log_message)

        return Response(response, status=status_code)


    # ----------------------------------------------------------------------------- #
    # Return a standardized error response for DRF API endpoints.                   #
    #                                                                               #
    # Creates a DRF Response with 'detail' key (DRF convention) and logs the        #
    # error event. Used for all API endpoints across the application.               #
    #                                                                               #
    # Args:     message (str): Error message to display to user                     #
    #           errors (dict): Optional detailed error information                  #
    #           status_code (int): HTTP status code (default: 400)                  #
    #           log_extra (dict): Optional extra context for logging                #
    # Returns:  Response: DRF Response object                                       #
    # ----------------------------------------------------------------------------- #
    @staticmethod
    def error(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST, log_extra=None):
        response = {'detail': message}
        if errors:
            response['errors'] = errors

        # Log the error event
        log_message = f"Error response: {message}"
        if log_extra:
            logger.error(log_message, extra=log_extra)
        else:
            logger.error(log_message)

        return Response(response, status=status_code)
