"""Configuration from environment variables (Design 3.4). Secrets never enter the repository."""
from functools import lru_cache
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEV_JWT_SECRET = "dev-only-secret-change-me-0123456789abcdef"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://internsync:internsync@localhost:5433/internsync"
    jwt_secret: str = DEV_JWT_SECRET
    frontend_base_url: str = "http://localhost:5173"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]  # comma-separated in the environment

    storage_backend: str = "local"  # local | supabase
    local_storage_dir: str = "./storage"
    supabase_url: str = ""
    supabase_service_key: str = ""
    storage_bucket: str = "internsync-files"

    mail_backend: str = "smtp"  # smtp | memory | console
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = False
    mail_from: str = "InternSync <no-reply@internsync.local>"

    scheduler_enabled: bool = False

    vapid_public_key: str = ""  # web push (FR-PWA-02); `python -m app.cli vapid-keys` makes a pair
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:no-reply@internsync.local"

    ai_enabled: bool = True
    embedding_model: str = "intfloat/multilingual-e5-small"

    @field_validator("database_url")
    @classmethod
    def use_psycopg(cls, v: str) -> str:
        """Accept the plain postgresql:// address that hosted databases show (the driver is psycopg 3)."""
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v.removeprefix(prefix)
        return v

    @model_validator(mode="after")
    def production_needs_a_secret(self):
        if self.env == "production" and (self.jwt_secret == DEV_JWT_SECRET or len(self.jwt_secret) < 32):
            raise ValueError("JWT_SECRET must be set to a random value of at least 32 characters in production")
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
