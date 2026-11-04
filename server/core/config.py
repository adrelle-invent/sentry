from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    DEBUG: bool = False

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    DB_CONNECTION: str = "postgresql+asyncpg"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_DATABASE: str = ""
    DB_USERNAME: str = ""
    DB_PASSWORD: str = ""

    DB_ECHO_LOG: bool = False

    @property
    def database_url(self) -> str:
        return (
            f"{self.DB_CONNECTION}://{self.DB_USERNAME}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        )


settings = Settings()