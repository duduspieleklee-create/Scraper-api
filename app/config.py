from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    POSTGRES_PASSWORD: Optional[str] = "postgres"

    # JWT Auth
    JWT_SECRET: str = secrets.token_hex(32)  # Fallback fuer Entwicklung, in Prod als Env setzen!

    # Scraper-Einstellungen
    REQUEST_DELAY_MIN: float = 1.5
    REQUEST_DELAY_MAX: float = 4.0
    REQUEST_TIMEOUT: int = 30

    # Token-Settings
    MIN_REQUIRED_BALANCE: int = 5


settings = Settings()
