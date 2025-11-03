"""
Backend Services

This module contains all service classes that implement the business logic
of the GW2Optimizer application. Services handle operations that involve
multiple models or require external interactions.
"""

# Import all services to make them available at the package level
from .ai_service import AIService  # noqa: F401
from .gw2_api import GW2APIService  # noqa: F401
from .mcm_analytics import McMAnalyticsService  # noqa: F401
from .user_service import UserService  # noqa: F401
from .team_service_db import TeamServiceDB  # noqa: F401
from .build_service_db import BuildServiceDB  # noqa: F401
from .email_service import send_verification_email  # noqa: F401
from .scheduler import scheduler  # noqa: F401

__all__ = [
    'AIService',
    'GW2APIService',
    'McMAnalyticsService',
    'UserService',
    'TeamServiceDB',
    'BuildServiceDB',
    'send_verification_email',
    'scheduler',
]
