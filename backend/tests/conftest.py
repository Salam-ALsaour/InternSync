"""Test fixtures (Increment 1 design, Section 11).

Tests run against a real PostgreSQL database (`internsync_test`, created on first use). The schema is built
once per session with Alembic; every test starts from empty tables, a frozen clock, and an empty mail outbox."""
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import pytest
from sqlalchemy.engine import make_url

BACKEND = Path(__file__).resolve().parents[1]
_STORAGE = tempfile.mkdtemp(prefix="internsync-test-")
TEST_DB = os.environ.get("TEST_DATABASE_URL",
                         "postgresql+psycopg://internsync:internsync@localhost:5433/internsync_test")
os.environ.update(ENV="test", DATABASE_URL=TEST_DB, MAIL_BACKEND="memory", LOCAL_STORAGE_DIR=_STORAGE,
                  SCHEDULER_ENABLED="false", JWT_SECRET="test-secret-0123456789abcdef0123456789abcdef")


def _ensure_database() -> None:
    url = make_url(TEST_DB)
    admin = url.set(drivername="postgresql", database="postgres").render_as_string(hide_password=False)
    with psycopg.connect(admin, autocommit=True) as conn:
        if conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (url.database,)).fetchone() is None:
            conn.execute(f'CREATE DATABASE "{url.database}"')


_ensure_database()

from argon2 import PasswordHasher  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.ai import skills as skill_index  # noqa: E402
from app.auth import service as auth_service  # noqa: E402
from app.core import clock, mail, security  # noqa: E402
from app.core.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from tests.factories import Factory  # noqa: E402

# Fast hashing in tests; production keeps the Argon2id library defaults.
security._hasher = PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)

# Sunday 25 October 2026, 09:00 in Riyadh.
T0 = datetime(2026, 10, 25, 6, 0, tzinfo=UTC)
TABLES = ", ".join(t.name for t in Base.metadata.sorted_tables)


@pytest.fixture(scope="session", autouse=True)
def schema():
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(cfg, "head")
    yield
    shutil.rmtree(_STORAGE, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean(schema):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
    mail.outbox.clear()
    auth_service._registrations.clear()
    skill_index.refresh_index()
    clock.reset()
    clock.freeze(T0)
    yield
    clock.reset()


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def f(db):
    return Factory(db)


@pytest.fixture
def w(f):
    """The standard world: two universities, three colleges, two companies, a user of every role, an open
    Co-op cycle in college A1 with two enrolled students, and a published vacancy of company 1."""
    return f.world()


def last_link(to: str | None = None) -> str:
    """The raw token of the last email sent (to `to`, when given)."""
    for message in reversed(mail.outbox):
        if to is None or message["to"].lower() == to.lower():
            return message["link"].rsplit("/", 1)[-1]
    raise AssertionError(f"no email to {to}")
