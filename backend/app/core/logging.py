"""Logging configuration."""

import logging
import sys
from pathlib import Path

from app.core.config import settings

try:
    import structlog
    
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

# Create logs directory if it doesn't exist
log_file_path = Path(settings.LOG_FILE)
log_file_path.parent.mkdir(parents=True, exist_ok=True)

# Configure structlog if available
if STRUCTLOG_AVAILABLE:
    # Processors for structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add JSON renderer for production, console for development
    if sys.stdout.isatty():
        # Development: colored console output
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # Production: JSON output for log aggregation
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.LOG_LEVEL.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Get structured logger
    logger = structlog.get_logger("gw2optimizer")
else:
    # Fallback to standard logging if structlog not available
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(settings.LOG_FILE),
        ],
    )
    logger = logging.getLogger("gw2optimizer")
