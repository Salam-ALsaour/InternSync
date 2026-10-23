"""Development-only endpoints (Increment 1 design, Section 9). Mounted only when ENV is development or test.

The demo clock moves the server's time forward so the M3 demo can show late and missing reports without
waiting a week. Moving the clock past the idle timeout ends open sessions; users log in again."""
from datetime import timedelta

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core import clock

router = APIRouter(prefix="/dev", tags=["development"])


class ClockShift(BaseModel):
    hours: float = Field(gt=0, le=24 * 120)


def _state() -> dict:
    return {"now": clock.now(), "offset_hours": round(clock.offset().total_seconds() / 3600, 2)}


@router.get("/clock")
def get_clock() -> dict:
    return _state()


@router.post("/clock/advance")
def advance_clock(body: ClockShift) -> dict:
    clock.shift(timedelta(hours=body.hours))
    return _state()


@router.post("/clock/reset")
def reset_clock() -> dict:
    clock.reset()
    return _state()
