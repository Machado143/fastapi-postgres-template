from typing import Literal

from pydantic import AnyUrl, BaseSettings, Field


class Settings(BaseSettings):
    # obrigatórios
    DATABASE_URL: AnyUrl
    JWT_SECRET_KEY: str

    # valores com default razoável
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, ge=1)
    DEBUG: bool = False
    ENV: Literal["dev", "staging", "production"] = "dev"
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, ge=1)

    class Config:
        # lê automaticamente .env na raiz do projeto
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# instância única para ser reutilizada
settings = Settings()
