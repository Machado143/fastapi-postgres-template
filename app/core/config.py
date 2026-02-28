from typing import Literal

from pydantic import AnyUrl, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- required ---
    DATABASE_URL: AnyUrl
    SECRET_KEY: str  # used by security.py for JWT signing

    # --- optional with defaults ---
    ALGORITHM: str = "HS256"  # JWT algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, ge=1)
    DEBUG: bool = False
    ENV: Literal["dev", "staging", "production"] = "dev"
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, ge=1)
    DB_CONNECT_TIMEOUT: int = Field(5, ge=1)

    class Config:
        # reads .env file at project root automatically
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @field_validator("DATABASE_URL", mode="before")
    def _ensure_asyncpg_prefix(cls, v: str) -> str:
        # Railway provides postgresql://, SQLAlchemy async requires +asyncpg
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @model_validator(mode="before")
    def _disable_debug_in_production(cls, values: dict) -> dict:
        # always force DEBUG=False in production regardless of env input
        if values.get("ENV") == "production":
            values["DEBUG"] = False
        return values


# singleton — imported everywhere as `from app.core.config import settings`
settings = Settings()
