"""Configuration from environment variables (Design 3.4). Secrets never enter the repository."""
from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://internsync:internsync@localhost:5433/internsync"
    jwt_secret: str = "dev-only-secret-change-me-0123456789abcdef"
    frontend_base_url: str = "http://localhost:5173"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]  # comma-separated in the environment

    storage_backend: str = "local"
    local_storage_dir: str = "./storage"

    mail_backend: str = "smtp"  # smtp | memory | console
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = False
    mail_from: str = "InternSync <no-reply@internsync.local>"

    scheduler_enabled: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
