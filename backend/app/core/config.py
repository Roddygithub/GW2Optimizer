"""Application configuration."""

import json
import os
from typing import Any, List, Optional, TYPE_CHECKING, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore[misc]
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
    SECRET_KEY: str
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
    LEARNING_DATA_DIR: str = "backend/data/learning/feedback"
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

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @field_validator("SECRET_KEY")  # type: ignore[misc]
    @classmethod
    def validate_secret(cls, value: str) -> str:
        if not value or len(value.strip()) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        if "your-secret-key" in value:
            raise ValueError("SECRET_KEY must be replaced with a strong random value")
        return value

    @model_validator(mode="before")  # type: ignore[misc]
    @classmethod
    def _hydrate_allowed_origins(cls, values: dict[str, Any]) -> dict[str, Any]:
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

    @field_validator("ALLOWED_ORIGINS", mode="before")  # type: ignore[misc]
    @classmethod
    def _coerce_origins(cls, value: Any) -> Any:
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

    @field_validator("COOKIE_SAMESITE", mode="after")  # type: ignore[misc]
    @classmethod
    def _normalize_samesite(cls, value: str) -> str:
        return (value or "lax").lower()

    @model_validator(mode="after")  # type: ignore[misc]
    def _apply_environment_cookie_defaults(self) -> Self:
        if self.is_production:
            self.COOKIE_SECURE = True
            self.COOKIE_SAMESITE = "strict"
        return self

    @model_validator(mode="after")  # type: ignore[misc]
    def _auto_disable_redis(self) -> Self:
        if self.REDIS_ENABLED and self.REDIS_URL:
            try:
                import redis
                r = redis.from_url(self.REDIS_URL)
                r.ping()
            except Exception:
                self.REDIS_ENABLED = False
        return self


if TYPE_CHECKING:
    settings: Settings = Settings(SECRET_KEY="x" * 32)
else:
    settings = Settings()
