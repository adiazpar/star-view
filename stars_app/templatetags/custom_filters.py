# ----------------------------------------------------------------------------------------------------- #
# This custom_filters.py file contains custom Django template filters that extend template              #
# functionality beyond built-in capabilities:                                                           #
#                                                                                                       #
# Filter Registration:                                                                                  #
# These filters are automatically registered when this module is loaded in templates. The @register     #
# decorator adds each function to Django's template filter library.                                     #
#                                                                                                       #
# Why Custom Filters are Needed:                                                                        #
# Django templates intentionally limit Python functionality for security and separation of concerns.    #
# These filters provide safe ways to perform operations that aren't possible with built-in tags:        #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django import template

# Register this module as a Django template filter library:
register = template.Library()



# ----------------------------------------------------------------------------- #
# Check if a location has been favorited by the current user.                   #
#                                                                               #
# This filter queries the Location model's favorited_by relationship to         #
# determine if the current user has favorited this location.                    #
#                                                                               #
# Args:       location: Location model instance to check                        #
#             user: User model instance (current authenticated user)            #
#                                                                               #
# Returns:    bool: True if user has favorited this location, False otherwise   #
#                                                                               #
# ----------------------------------------------------------------------------- #
@register.filter
def is_favorite(location, user):
    # Only check for authenticated users:
    if user.is_authenticated:
        # Query the favorited_by relationship to check if this user has favorited this location:
        return location.favorited_by.filter(user=user).exists()

    # Return False for unauthenticated users:
    return False


# ----------------------------------------------------------------------------- #
# Retrieve a value from a dictionary using a key in Django templates.           #
#                                                                               #
# Django templates don't support bracket notation (dict[key]), so this filter   #
# provides a way to access dictionary values dynamically. It intelligently      #
# tries multiple key types (original, string, integer) to handle type           #
# mismatches that can occur when passing variables through templates.           #
#                                                                               #
# Args:       dictionary: Dictionary to retrieve value from                     #
#             key: Key to look up (can be any type)                             #
#                                                                               #
# Returns:    The value at dictionary[key], or None if not found                #
#                                                                               #
# ----------------------------------------------------------------------------- #

@register.filter
def get_item(dictionary, key):
    # Handle None or empty dictionary:
    if not dictionary:
        return None

    # Try to get the value using the key as-is:
    result = dictionary.get(key)
    if result is None:
        # If not found, try converting key to string:
        result = dictionary.get(str(key))
    if result is None:
        # If still not found, try converting key to integer:
        try:
            result = dictionary.get(int(str(key)))
        except (ValueError, TypeError):
            # Key cannot be converted to integer, return None:
            pass

    return result
