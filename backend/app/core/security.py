"""Password hashing (Argon2id), JWT access tokens, and one-time link tokens (Design 7.1)."""
import hashlib
import re
import secrets
import uuid
from datetime import datetime

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()  # Argon2id with library defaults


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(hash_: str | None, password: str) -> bool:
    if not hash_:
        return False
    try:
        return _hasher.verify(hash_, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_is_strong(password: str, min_length: int = 8) -> bool:
    return len(password) >= min_length and bool(re.search(r"[A-Za-z؀-ۿ]", password)) \
        and bool(re.search(r"\d", password))


def create_access_token(user_id: uuid.UUID, role: str, session_id: uuid.UUID, issued: datetime,
                        expires: datetime) -> str:
    payload = {"sub": str(user_id), "role": role, "sid": str(session_id),
               "iat": int(issued.timestamp()), "exp": int(expires.timestamp())}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm="HS256")


def decode_access_token(token: str, at: datetime) -> dict | None:
    """Signature and expiry are checked against the application clock, not the system clock."""
    try:
        data = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"],
                          options={"verify_exp": False, "verify_iat": False, "verify_nbf": False})
    except jwt.PyJWTError:
        return None
    if int(data.get("exp", 0)) <= int(at.timestamp()):
        return None
    return data


def new_link_token() -> tuple[str, str]:
    """32 random bytes, URL-safe; only the SHA-256 hash is stored."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
