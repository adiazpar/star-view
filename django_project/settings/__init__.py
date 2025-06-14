"""
Settings module for Event Horizon Django project.
Automatically loads the appropriate settings based on ENVIRONMENT variable.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Determine which settings to use
environment = os.getenv('ENVIRONMENT', 'development').lower()

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .staging import *
else:
    from .development import *