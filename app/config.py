from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kleinanzeigen"  # Default für lokal
    POSTGRES_PASSWORD: Optional[str] = "postgres"


    # Scraper-Einstellungen
    REQUEST_DELAY_MIN: float = 1.5
    REQUEST_DELAY_MAX: float = 4.0
    REQUEST_TIMEOUT: int = 30

    # Token-Settings
    MIN_REQUIRED_BALANCE: int = 5

settings = Settings()
