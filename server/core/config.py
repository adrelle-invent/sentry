from typing import Literal

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "AD. Sentry"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

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

    DB_ECHO_LOG: bool = False

    @computed_field
    @property
    def database_url(self) -> str:
        """Derives the async database URL securely, safely unmasking the password."""
        return (
            f"{self.DB_CONNECTION}://{self.DB_USERNAME}:{self.DB_PASSWORD.get_secret_value()}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        )

settings = Settings()
