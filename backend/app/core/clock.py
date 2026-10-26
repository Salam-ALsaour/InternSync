"""The only source of time in the application (Design 5.2). Tests freeze and move it."""
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

RIYADH = ZoneInfo("Asia/Riyadh")
_frozen: datetime | None = None
_offset = timedelta(0)


def now() -> datetime:
    """Current time in UTC (timezone-aware)."""
    return _frozen if _frozen is not None else datetime.now(UTC) + _offset


def freeze(at: datetime | None) -> None:
    """Freeze the clock at `at` (UTC-aware) or unfreeze with None. For tests and the demo only."""
    global _frozen
    if at is not None and at.tzinfo is None:
        raise ValueError("freeze() needs a timezone-aware datetime")
    _frozen = at.astimezone(UTC) if at is not None else None


def advance(delta: timedelta) -> None:
    freeze(now() + delta)


def shift(delta: timedelta) -> None:
    """Move a running clock by `delta` without stopping it. Used by the development-only clock endpoint."""
    global _offset
    _offset += delta


def offset() -> timedelta:
    return _offset


def reset() -> None:
    global _frozen, _offset
    _frozen, _offset = None, timedelta(0)


def riyadh_to_utc(d: date, t: time) -> datetime:
    """A local Asia/Riyadh date and time converted to UTC."""
    return datetime.combine(d, t, tzinfo=RIYADH).astimezone(UTC)


def today_riyadh() -> date:
    return now().astimezone(RIYADH).date()
