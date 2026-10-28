"""The notification outbox and the in-app list (FR-NOT-01, FR-NOT-05, FR-NOT-06; Increment 3 design, Section 5).

`notify` writes one row per recipient in the caller's transaction, so a notification exists exactly when the change
that caused it was saved. A repeated idempotency key is ignored, so jobs that run twice send nothing twice
(NFR-REL-03)."""
import uuid
from collections.abc import Iterable

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core import clock
from app.core.common import PageParams, paginate
from app.core.errors import not_found
from app.models import Notification, User
from app.notifications.texts import render


def notify(db: Session, users: Iterable[uuid.UUID | User | None], event: str, params: dict | None = None,
           link: str | None = None, key: str | None = None) -> int:
    """Queue `event` for each active user in `users`; `key` makes it once per user (the user id is appended)."""
    ids = list(dict.fromkeys(u.id if isinstance(u, User) else u for u in users if u is not None))
    if not ids:
        return 0
    active = db.scalars(select(User.id).where(User.id.in_(ids), User.is_active)).all()
    created = 0
    for user_id in active:
        stmt = insert(Notification).values(
            id=uuid.uuid4(), user_id=user_id, event=event, params=params or {}, link=link,
            idempotency_key=f"{key}:{user_id}" if key else None, created_at=clock.now())
        created += db.execute(stmt.on_conflict_do_nothing(index_elements=["idempotency_key"])).rowcount
    return created


def coordinator_of(db: Session, college_id: uuid.UUID | None) -> User | None:
    if college_id is None:
        return None
    return db.scalar(select(User).where(User.college_id == college_id, User.role == "coordinator",
                                        User.verification_status == "verified", User.is_active))


def platform_admins(db: Session) -> list[User]:
    return list(db.scalars(select(User).where(User.role == "platform_admin", User.is_active)))


def item_out(n: Notification, lang: str) -> dict:
    title, body = render(n.event, n.params, lang)
    return {"id": n.id, "event": n.event, "title": title, "body": body, "link": n.link, "read_at": n.read_at,
            "created_at": n.created_at}


def unread_count(db: Session, user: User) -> int:
    return db.scalar(select(func.count()).select_from(Notification).where(
        Notification.user_id == user.id, Notification.read_at.is_(None))) or 0


def listing(db: Session, user: User, unread_only: bool, params: PageParams) -> dict:
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    page = paginate(db, stmt.order_by(Notification.created_at.desc(), Notification.id), params,
                    lambda n: item_out(n, user.language))
    return {**page, "unread_count": unread_count(db, user)}


def mark_read(db: Session, user: User, notification_id: uuid.UUID) -> dict:
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user.id:
        raise not_found()
    if n.read_at is None:
        n.read_at = clock.now()
    return item_out(n, user.language)


def mark_all_read(db: Session, user: User) -> int:
    return db.execute(update(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
                      .values(read_at=clock.now())).rowcount
