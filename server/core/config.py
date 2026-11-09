from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        env_ignore_empty=True,
    )

    # Application
    APP_NAME: str = "AD. Sentry"
    APP_ENV: Literal["local", "staging", "production"] = "local"
    DEBUG: bool = False

    # CORS - Parsed safely as a list
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        description="Comma-separated or JSON list of allowed CORS origins"
    )

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535)

    # Database
    DB_CONNECTION: str = "postgresql+asyncpg"
    DB_HOST: str = "localhost"
    DB_PORT: int = Field(default=5432, ge=1, le=65535)
    DB_DATABASE: str
    DB_USERNAME: str
    DB_PASSWORD: SecretStr

    @property
    def database_url(self) -> str:
        """Derives the async database URL securely without exposing plaintext in serialization."""
        return (
            f"{self.DB_CONNECTION}://{self.DB_USERNAME}:{self.DB_PASSWORD.get_secret_value()}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        )


settings = Settings()