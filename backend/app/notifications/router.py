"""API 3.17 – Notifications and push (FR-NOT-01, FR-PWA-02)."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.common import PageParams
from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.models import PushSubscription
from app.notifications import service

router = APIRouter(tags=["notifications"])
ANY = auth(unverified=True)  # verification results reach accounts that are not verified yet


class NotificationOut(BaseModel):
    id: uuid.UUID
    event: str
    title: str
    body: str
    link: str | None
    read_at: datetime | None
    created_at: datetime


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    page: int
    page_size: int
    total: int
    unread_count: int


class UnreadCount(BaseModel):
    unread_count: int


class VapidKey(BaseModel):
    key: str | None


class SubscriptionKeys(BaseModel):
    p256dh: str = Field(min_length=1, max_length=200)
    auth: str = Field(min_length=1, max_length=100)


class SubscriptionIn(BaseModel):
    endpoint: str = Field(min_length=10, max_length=1000, pattern=r"^https://")
    keys: SubscriptionKeys


class SubscriptionRef(BaseModel):
    endpoint: str = Field(min_length=10, max_length=1000)


@router.get("/notifications", response_model=NotificationPage)
def list_notifications(unread_only: bool = False, params: PageParams = Depends(), actor: Actor = Depends(ANY),
                       db: Session = Depends(get_db)):
    return service.listing(db, actor.user, unread_only, params)


@router.post("/notifications/read-all", response_model=UnreadCount)
def read_all(actor: Actor = Depends(ANY), db: Session = Depends(get_db)):
    service.mark_all_read(db, actor.user)
    db.commit()
    return {"unread_count": 0}


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def read_one(notification_id: uuid.UUID, actor: Actor = Depends(ANY), db: Session = Depends(get_db)):
    out = service.mark_read(db, actor.user, notification_id)
    db.commit()
    return out


@router.get("/push/vapid-public-key", response_model=VapidKey)
def vapid_public_key(actor: Actor = Depends(ANY)):
    return {"key": get_settings().vapid_public_key or None}


@router.post("/push/subscriptions", status_code=204)
def subscribe(body: SubscriptionIn, actor: Actor = Depends(ANY), db: Session = Depends(get_db)):
    sub = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == body.endpoint))
    if sub is None:
        db.add(PushSubscription(user_id=actor.id, endpoint=body.endpoint, p256dh=body.keys.p256dh,
                                auth=body.keys.auth))
    else:  # the same browser signed in as another user, or new keys
        sub.user_id, sub.p256dh, sub.auth = actor.id, body.keys.p256dh, body.keys.auth
    db.commit()
    return Response(status_code=204)


@router.delete("/push/subscriptions", status_code=204)
def unsubscribe(body: SubscriptionRef, actor: Actor = Depends(ANY), db: Session = Depends(get_db)):
    db.execute(delete(PushSubscription).where(PushSubscription.endpoint == body.endpoint,
                                              PushSubscription.user_id == actor.id))
    db.commit()
    return Response(status_code=204)
