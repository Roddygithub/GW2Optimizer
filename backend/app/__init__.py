"""
GW2Optimizer Backend Application

This package contains the main application code for the GW2Optimizer backend,
including API endpoints, services, agents, and workflows for optimizing Guild Wars 2 gameplay.
"""

# Import core modules to make them available at the package level
from app.core import (  # noqa: F401
    settings,
    logger,
    CacheManager,
    cacheable,
    invalidate_cache,
    CircuitBreaker,
    CircuitBreakerError,
    get_redis_client,
    connect_to_redis,
)

# Import services
from app.services import (  # noqa: F401
    AIService,
    GW2APIService,
    McMAnalyticsService,
    UserService,
    TeamServiceDB,
    BuildServiceDB,
)

# Import models
from app.models import (  # noqa: F401
    User,
    TeamComposition,
    Build,
    GameMode,
    Role,
    Profession,
)

# Import API routers
from app.api import (  # noqa: F401
    auth_router,
    builds_router,
    teams_router,
    ai_router,
    meta_router,
    health_router,
)

# Make core modules available at the package level
__all__ = [
    # Core
    'settings',
    'logger',
    'CacheManager',
    'cacheable',
    'invalidate_cache',
    'CircuitBreaker',
    'CircuitBreakerError',
    'get_redis_client',
    'connect_to_redis',
    
    # Services
    'AIService',
    'GW2APIService',
    'McMAnalyticsService',
    'UserService',
    'TeamServiceDB',
    'BuildServiceDB',
    
    # Models
    'User',
    'TeamComposition',
    'Build',
    'GameMode',
    'Role',
    'Profession',
    
    # API Routers
    'auth_router',
    'builds_router',
    'teams_router',
    'ai_router',
    'meta_router',
    'health_router',
]
