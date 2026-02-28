from typing import Literal

from pydantic import AnyUrl, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # required
    DATABASE_URL: AnyUrl
    SECRET_KEY: str  # era JWT_SECRET_KEY — security.py usa settings.SECRET_KEY

    # reasonable defaults
    ALGORITHM: str = "HS256"  # era ausente — security.py usa settings.ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, ge=1)
    DEBUG: bool = False
    ENV: Literal["dev", "staging", "production"] = "dev"
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, ge=1)
    DB_CONNECT_TIMEOUT: int = Field(5, ge=1)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @field_validator("DATABASE_URL", mode="before")
    def _ensure_asyncpg_prefix(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @model_validator(mode="before")
    def _disable_debug_in_production(cls, values: dict) -> dict:
        if values.get("ENV") == "production":
            values["DEBUG"] = False
        return values


settings = Settings()
