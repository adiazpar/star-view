import re


# EMAIL VERIFICATION ------------------------------------------------ #
def is_valid_email(email):
    # Validate email format and domain:
    if not email:
        return False

    # Basic email validation pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
