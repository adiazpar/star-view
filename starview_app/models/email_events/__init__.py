# ----------------------------------------------------------------------------------------------------- #
# Email Events Package - AWS SES Bounce and Complaint Tracking                                          #
#                                                                                                       #
# Purpose:                                                                                              #
# Package for email deliverability monitoring models that integrate with AWS SES.                       #
# Provides centralized imports for all email event tracking models.                                     #
#                                                                                                       #
# Models:                                                                                               #
# - EmailBounce: Tracks bounced emails (hard/soft/transient)                                            #
# - EmailComplaint: Tracks spam complaints from recipients                                              #
# - EmailSuppressionList: Master list for email suppression management                                  #
#                                                                                                       #
# Integration:                                                                                          #
# AWS SES → AWS SNS → Django webhook endpoints → These models                                           #
#                                                                                                       #
# Usage:                                                                                                #
#   from starview_app.models import EmailBounce, EmailComplaint, EmailSuppressionList                   #
# ----------------------------------------------------------------------------------------------------- #

from .model_email_bounce import EmailBounce
from .model_email_complaint import EmailComplaint
from .model_email_suppressionlist import EmailSuppressionList

__all__ = [
    'EmailBounce',
    'EmailComplaint',
    'EmailSuppressionList',
]
