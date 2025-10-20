"""Logging configuration."""

import logging
import sys
from pathlib import Path

from app.core.config import settings

# Create logs directory if it doesn't exist
log_file_path = Path(settings.LOG_FILE)
log_file_path.parent.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE),
    ],
)

logger = logging.getLogger("gw2optimizer")
