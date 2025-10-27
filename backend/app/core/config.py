"""Application configuration."""

import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Backend Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Ollama Configuration
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral:7b"

    # Database
    DATABASE_PATH: str = "./data/local_db/gw2optimizer.db"

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./gw2optimizer.db"
    DATABASE_ECHO: bool = False

    # API Configuration
    API_VERSION: str = "v1"
    API_V1_STR: str = "/api/v1"
    API_PREFIX: str = "/api/v1"

    # Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    OLD_SECRET_KEYS: List[str] = []  # For key rotation
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token"
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT: str = "50/minute"
    REGISTRATION_RATE_LIMIT: str = "10/hour"
    REGISTRATION_RATE_LIMIT_COUNT: int = 10
    REGISTRATION_RATE_LIMIT_WINDOW_SECONDS: int = 3600
    PASSWORD_RECOVERY_RATE_LIMIT: str = "5/hour"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # AI Configuration
    AI_MODEL_NAME: str = "gpt-4"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 2048

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"

    # Scraping Configuration
    SCRAPER_UPDATE_INTERVAL: int = 604800  # 7 days in seconds
    SCRAPER_USER_AGENT: str = "GW2Optimizer/1.0"

    # Cache Configuration
    CACHE_TTL: int = 3600  # 1 hour in seconds
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    # Testing
    TESTING: bool = bool(os.getenv("PYTEST_CURRENT_TEST"))
    LOG_FILE: str = "logs/gw2optimizer.log"
    ACCOUNT_LOCK_DURATION_MINUTES: int = 15
    ENFORCE_ACCOUNT_LOCKS_IN_TESTS: bool = True
    ENABLE_HTTPS_REDIRECT: bool = False

    # Learning Configuration
    LEARNING_DATA_DIR: str = "./data/learning"
    MAX_LEARNING_ITEMS: int = 10000
    LEARNING_ENABLED: bool = True

    # AI Core Configuration (v4.1.0)
    AI_CORE_ENABLED: bool = True  # Feature flag for AI Core
    MISTRAL_API_KEY: str | None = None  # Mistral AI API key
    AI_TIMEOUT: float = 2.0  # Timeout for AI requests in seconds
    AI_RATE_LIMIT: int = 60  # Max requests per minute for /compose endpoint
    ML_TRAINING_ENABLED: bool = False  # Feature flag for ML training in prod
    AI_FALLBACK_ENABLED: bool = True  # Use rule-based fallback if AI fails

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
