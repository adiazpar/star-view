# ----------------------------------------------------------------------------------------------------- #
# This __init__.py file marks the templatetags directory as a Python package (intentionally empty):     #
#                                                                                                       #
# Why This File Exists:                                                                                 #
# Django REQUIRES this file to recognize the directory as a valid template tags library. Without it,    #
# Django won't discover custom template tags and filters defined in this directory.                     #
#                                                                                                       #
# Template Tags Discovery:                                                                              #
# Django's template system looks for template tag modules in any app that has a 'templatetags'          #
# directory with an __init__.py file. Each module (like custom_filters.py) becomes loadable via:        #
# {% load custom_filters %} in templates.                                                               #
#                                                                                                       #
# Directory Contents:                                                                                   #
# - custom_filters.py: Custom template filters for formatting and display logic                         #
#                                                                                                       #
# Usage in Templates:                                                                                   #
# {% load custom_filters %}                                                                             #
# {{ value|filter_name }}                                                                               #
#                                                                                                       #
# Note: This file must remain empty (or contain only comments). Django autodiscovery handles            #
# registration of template tags defined in modules within this directory.                               #
# ----------------------------------------------------------------------------------------------------- #