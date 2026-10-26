"""Configuration from the environment (Design 3.4)."""
import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_accept_a_comma_separated_list(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, https://internsync.example.org")
    assert Settings().cors_origins == ["http://localhost:5173", "https://internsync.example.org"]


def test_cors_origins_accept_a_single_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")
    assert Settings().cors_origins == ["http://localhost:5173"]


def test_plain_postgres_address_uses_psycopg(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@aws-0-eu.pooler.supabase.com:5432/postgres?sslmode=require")
    assert Settings().database_url == "postgresql+psycopg://u:p@aws-0-eu.pooler.supabase.com:5432/postgres?sslmode=require"
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost/x")
    assert Settings().database_url == "postgresql+psycopg://u:p@localhost/x"


def test_production_refuses_the_development_secret(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    assert Settings(_env_file=None).env == "production"
