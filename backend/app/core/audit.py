"""Audit entries, written in the same transaction as the change they describe (FR-AUD-01, Design 2.3)."""
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import AuditEntry, User


def _plain(value):
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple | set):
        return [_plain(v) for v in value]
    if isinstance(value, uuid.UUID | datetime | date | time | Decimal):
        return str(value)
    return value


def record(db: Session, actor: User | None, action: str, entity_type: str, entity_id, *,
           student_id=None, college_id=None, company_id=None, cycle_id=None,
           old: dict | None = None, new: dict | None = None, reason: str | None = None) -> None:
    db.add(AuditEntry(
        user_id=actor.id if actor else None,
        role=actor.role if actor else "system",
        action=action, entity_type=entity_type, entity_id=str(entity_id),
        student_id=student_id, college_id=college_id, company_id=company_id, cycle_id=cycle_id,
        old_value=_plain(old) if old else None, new_value=_plain(new) if new else None, reason=reason,
    ))


def changes(obj, values: dict) -> tuple[dict, dict]:
    """Apply `values` to `obj` and return (old, new) for the fields that really changed."""
    old, new = {}, {}
    for key, value in values.items():
        current = getattr(obj, key)
        if current != value:
            old[key], new[key] = current, value
            setattr(obj, key, value)
    return old, new
