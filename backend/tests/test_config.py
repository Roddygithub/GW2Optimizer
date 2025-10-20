"""Test configuration."""

import os
from typing import Dict, Any

from pydantic import PostgresDsn, validator
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    """Test settings."""

    # Database
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    TEST_DATABASE_ECHO: bool = True
    TEST_DATABASE_POOL_SIZE: int = 5
    TEST_DATABASE_MAX_OVERFLOW: int = 10
    TEST_DATABASE_POOL_PRE_PING: bool = True
    TEST_DATABASE_POOL_RECYCLE: int = 300

    # Security
    TEST_SECRET_KEY: str = "test-secret-key"
    TEST_ALGORITHM: str = "HS256"
    TEST_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    TEST_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        """Pydantic config."""

        env_file = ".env.test"
        case_sensitive = True


# Create test settings instance
test_settings = TestSettings()
