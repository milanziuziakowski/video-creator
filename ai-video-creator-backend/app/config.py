"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "AI Video Creator"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # API Keys
    OPENAI_API_KEY: str = ""
    MINIMAX_API_KEY: str = ""

    # JWT Authentication
    # Generate a secret key with: openssl rand -hex 32
    JWT_SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./video_creator.db"

    # Storage
    STORAGE_PATH: Path = Path("./storage")
    UPLOAD_MAX_SIZE_MB: int = 20

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins as list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def storage_uploads(self) -> Path:
        """Get uploads directory path."""
        path = self.STORAGE_PATH / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def storage_temp(self) -> Path:
        """Get temp directory path."""
        path = self.STORAGE_PATH / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def storage_output(self) -> Path:
        """Get output directory path."""
        path = self.STORAGE_PATH / "output"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.APP_ENV == "development"


settings = Settings()
