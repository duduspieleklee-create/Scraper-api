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

    def assemble_db_connection(uri):
        return Settings.DATABASE_URL(uri, "postgresql+asyncpg://", 1)

    # JWT Auth
    JWT_SECRET: str = secrets.token_hex(32)

    # Scraper-Einstellungen
    REQUEST_DELAY_MIN: float = 1.5
    REQUEST_DELAY_MAX: float = 4.0
    REQUEST_TIMEOUT: int = 30

    # Token-Settings
    TOKEN_COST_PER_RUN: int = 5
    MAX_EXECUTIONS_PER_MINUTE: int = 5
    
    # Payment Gateway Webhook Secret
    PAYMENT_SECRET: str = secrets.token_hex(32)
    
    # Token Pricing by interval (in minutes)
    @property
    def INTERVAL_PRICING(self) -> dict:
        return {
            1: 5,
            15: 3,
            60: 2,
            180: 1,
        }


settings = Settings()