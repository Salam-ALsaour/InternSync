"""Request pipeline as dependencies (Design 2.3): session → consent gate → verification gate → role.
Role and gate failures are raised before the request body is validated, so callers without the right role
get 401 or 403, never 422 (permission matrix)."""
import uuid
from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core import clock, settings
from app.core.db import get_db
from app.core.errors import ApiError
from app.core.i18n import set_language
from app.core.security import decode_access_token
from app.models import User, UserSession

ROLE_CODE = {"student": "st", "company_supervisor": "cs", "academic_supervisor": "as", "coordinator": "co",
             "platform_admin": "pa"}


@dataclass
class Actor:
    user: User
    session: UserSession

    @property
    def code(self) -> str:
        return ROLE_CODE[self.user.role]

    @property
    def is_ca(self) -> bool:
        return self.user.role == "company_supervisor" and self.user.is_company_admin

    def has(self, *roles: str) -> bool:
        return self.code in roles or ("ca" in roles and self.is_ca)

    @property
    def id(self) -> uuid.UUID:
        return self.user.id


def authenticate(request: Request, db: Session) -> Actor:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise ApiError(401, "UNAUTHENTICATED")
    now = clock.now()
    data = decode_access_token(header[7:].strip(), now)
    if data is None:
        raise ApiError(401, "SESSION_EXPIRED")
    try:
        sid, uid = uuid.UUID(data["sid"]), uuid.UUID(data["sub"])
    except (KeyError, ValueError) as exc:
        raise ApiError(401, "UNAUTHENTICATED") from exc
    session = db.get(UserSession, sid)
    if session is None or session.revoked_at is not None or session.user_id != uid:
        raise ApiError(401, "SESSION_EXPIRED")
    idle = timedelta(minutes=settings.get(db, "auth.idle_timeout_minutes"))
    if now - session.last_seen_at > idle or now >= session.expires_at:
        session.revoked_at = now
        session.revoke_reason = "idle" if now < session.expires_at else "expired"
        db.commit()
        raise ApiError(401, "SESSION_EXPIRED")
    user = db.get(User, uid)
    if user is None or not user.is_active:
        raise ApiError(401, "SESSION_EXPIRED")
    if now - session.last_seen_at >= timedelta(minutes=1):
        session.last_seen_at = now
        db.commit()
    set_language(user.language)
    request.state.lang = user.language
    return Actor(user, session)


def auth(*roles: str, unverified: bool = False, consent: bool = True):
    """Dependency factory. `roles` uses the codes st, cs, ca, as, co, pa; empty means any role."""
    def dependency(request: Request, db: Session = Depends(get_db)) -> Actor:
        actor = authenticate(request, db)
        if consent and actor.user.consent_at is None:
            raise ApiError(403, "CONSENT_REQUIRED")
        if not unverified and actor.user.verification_status in ("pending", "rejected"):
            raise ApiError(403, "VERIFICATION_REQUIRED")
        if roles and not actor.has(*roles):
            raise ApiError(403, "FORBIDDEN")
        return actor
    dependency.roles = roles  # read by the permission-matrix test
    dependency.unverified = unverified
    return dependency
