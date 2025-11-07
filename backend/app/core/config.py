"""Application configuration."""

import json
import os
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
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
    REQUIRE_POSTGRES: bool = False

    # API Configuration
    API_VERSION: str = "v1"
    API_V1_STR: str = "/api/v1"
    API_PREFIX: str = "/api/v1"
    BASE_URL_BACKEND: str = "http://localhost:8000"

    # Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    OLD_SECRET_KEYS: List[str] = []  # For key rotation

    # GW2 Sync Configuration
    GW2_SYNC_OPEN: bool = False  # If True, allows unauthenticated access to the sync endpoint
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
    DEFAULT_RATE_LIMIT: str = "60/minute"

    # CORS / Frontend Origins
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # Cookie configuration (dev defaults; harden in production via env)
    COOKIE_DOMAIN: Optional[str] = None
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_MAX_AGE: Optional[int] = None

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

    @model_validator(mode="before")
    @classmethod
    def _hydrate_allowed_origins(cls, values: dict) -> dict:
        if values.get("ALLOWED_ORIGINS"):
            return values

        legacy = values.get("CORS_ORIGINS") or values.get("BACKEND_CORS_ORIGINS")
        if not legacy:
            return values

        if isinstance(legacy, str):
            items = [item.strip() for item in legacy.split(",") if item.strip()]
        else:
            items = list(legacy)

        values["ALLOWED_ORIGINS"] = items
        return values

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _coerce_origins(cls, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item).strip("/") for item in parsed]
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, (tuple, list)):
            return [str(item).strip("/") for item in value]
        return value

    @field_validator("COOKIE_SAMESITE", mode="after")
    @classmethod
    def _normalize_samesite(cls, value: str) -> str:
        return (value or "lax").lower()


settings = Settings()
