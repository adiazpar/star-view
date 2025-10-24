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
