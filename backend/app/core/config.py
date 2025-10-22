"""Application configuration."""

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
    OLLAMA_MODEL: str = "mistral:latest"

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

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Scraping Configuration
    SCRAPER_UPDATE_INTERVAL: int = 604800  # 7 days in seconds
    SCRAPER_USER_AGENT: str = "GW2Optimizer/1.0"

    # Cache Configuration
    CACHE_TTL: int = 3600  # 1 hour in seconds
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/gw2optimizer.log"

    # Learning Configuration
    LEARNING_DATA_DIR: str = "./data/learning"
    MAX_LEARNING_ITEMS: int = 10000
    LEARNING_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
