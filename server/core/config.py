import re
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,}$")


def validate_app_key(secret: SecretStr) -> SecretStr:
    raw = secret.get_secret_value()
    if not APP_KEY_PATTERN.fullmatch(raw):
        raise ValueError(
            "APP_KEY must be at least 32 URL-safe characters ([A-Za-z0-9_-])."
        )
    return secret


SecretAppKey = Annotated[SecretStr, AfterValidator(validate_app_key)]


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
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["local", "staging", "production"] = "local"
    APP_DEBUG: bool = True
    APP_KEY: SecretAppKey

    APP_HOST: str = "localhost"
    APP_PORT: int = 8000

    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

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

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, ge=1)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1)
    JWT_ALGORITHM: str = "HS256"


settings = Settings()
