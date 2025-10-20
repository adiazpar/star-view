# ----------------------------------------------------------------------------------------------------- #
# This __init__.py file marks stars_app as a Python package (intentionally empty):                      #
#                                                                                                       #
# Why This File Exists:                                                                                 #
# While Python 3.3+ doesn't strictly require __init__.py for packages (PEP 420 namespace packages),     #
# Django apps should be REGULAR packages, not namespace packages. This empty file ensures:              #
#                                                                                                       #
# 1. Django's app loading system properly recognizes and loads the app                                  #
# 2. Relative imports work correctly (from .models import Location)                                     #
# 3. Django's autodiscovery finds admin.py, signals.py, apps.py, etc.                                   #
# 4. Compatibility with third-party Django tools that expect regular packages                           #
#                                                                                                       #
# When to Add Content:                                                                                  #
# This file should remain empty unless you need:                                                        #
# - Package-level imports to expose models/functions at the package level                               #
# - Initialization code that runs when the package is first imported                                    #
# - Default app config (legacy Django): default_app_config = 'stars_app.apps.StarsAppConfig'            #
#                                                                                                       #
# Recommendation: Keep this file as-is (empty). It's standard practice for Django apps.                 #
# ----------------------------------------------------------------------------------------------------- #
