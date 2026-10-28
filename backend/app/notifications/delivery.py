"""Delivery of the outbox: email in the recipient's language and web push (FR-NOT-01, FR-NOT-06, FR-PWA-02).

Run by the `deliver_notifications` job every minute. An email is tried up to 5 times; push is `skipped` when the
VAPID keys are not configured or the user has no subscription, and email stays the fallback. The push payload is the
title and the link only (NFR-PRV-03)."""
import json
import logging
from collections import defaultdict
from collections.abc import Callable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core import clock, mail
from app.core.config import get_settings
from app.models import Notification, PushSubscription, User
from app.notifications.texts import GREETING, OPEN, render

log = logging.getLogger("internsync.notifications")
MAX_EMAIL_ATTEMPTS = 5
BATCH = 200


class Gone(Exception):
    """The push service no longer knows the subscription (404 or 410)."""


def _webpush(subscription: dict, data: str) -> None:
    from pywebpush import WebPushException, webpush

    settings = get_settings()
    try:
        webpush(subscription_info=subscription, data=data, vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject}, ttl=24 * 3600)
    except WebPushException as exc:
        if exc.response is not None and exc.response.status_code in (404, 410):
            raise Gone from exc
        raise


_sender: Callable[[dict, str], None] = _webpush


def set_sender(sender: Callable[[dict, str], None] | None) -> None:
    """Install a stand-in push sender (tests), or put the real one back."""
    global _sender
    _sender = sender or _webpush


def push_configured() -> bool:
    settings = get_settings()
    return bool(settings.vapid_public_key and settings.vapid_private_key)


def email_body(user: User, body: str, link: str | None) -> str:
    lang = "ar" if user.language == "ar" else "en"
    name = user.name_ar if lang == "ar" else user.name_en
    parts = [GREETING[lang].format(name=name), "", body]
    if link:
        parts += ["", f"{OPEN[lang]}: {get_settings().frontend_base_url.rstrip('/')}{link}"]
    return "\n".join(parts + ["", "InternSync"])


def _push(db: Session, subscriptions: list[PushSubscription], payload: dict) -> str:
    if not subscriptions or not push_configured():
        return "skipped"
    sent = False
    for sub in list(subscriptions):
        try:
            _sender({"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                    json.dumps(payload, ensure_ascii=False))
            sub.last_success_at, sent = clock.now(), True
        except Gone:
            db.delete(sub)
            subscriptions.remove(sub)
        except Exception:  # one broken endpoint must not stop the others
            log.exception("push to %s failed", sub.endpoint[:60])
    return "sent" if sent else "failed"


def deliver(db: Session) -> int:
    rows = db.scalars(select(Notification).where(or_(Notification.email_status == "pending",
                                                     Notification.push_status == "pending"))
                      .order_by(Notification.created_at).limit(BATCH).with_for_update(skip_locked=True)).all()
    if not rows:
        return 0
    user_ids = {n.user_id for n in rows}
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(user_ids)))}
    subscriptions = defaultdict(list)
    for sub in db.scalars(select(PushSubscription).where(PushSubscription.user_id.in_(user_ids))):
        subscriptions[sub.user_id].append(sub)
    now = clock.now()
    for n in rows:
        user = users[n.user_id]
        title, body = render(n.event, n.params, user.language)
        if n.email_status == "pending":
            if not user.is_active:
                n.email_status = "skipped"
            elif mail.deliver(user.email, title, email_body(user, body, n.link), template=n.event, link=n.link):
                n.email_status, n.emailed_at = "sent", now
                n.email_attempts += 1
            else:
                n.email_attempts += 1
                if n.email_attempts >= MAX_EMAIL_ATTEMPTS:
                    n.email_status = "failed"
        if n.push_status == "pending":
            n.push_status = _push(db, subscriptions[user.id], {"title": title, "link": n.link or "/"})
            if n.push_status == "sent":
                n.pushed_at = now
    return len(rows)
