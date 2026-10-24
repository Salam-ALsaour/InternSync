"""Configuration from the environment (Design 3.4)."""
from app.core.config import Settings


def test_cors_origins_accept_a_comma_separated_list(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, https://internsync.example.org")
    assert Settings().cors_origins == ["http://localhost:5173", "https://internsync.example.org"]


def test_cors_origins_accept_a_single_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")
    assert Settings().cors_origins == ["http://localhost:5173"]
