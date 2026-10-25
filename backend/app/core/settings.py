"""Configurable defaults stored in system_settings (NFR-MNT-03, Design Table 4.1). Values are numbers: whole
numbers where the default is whole, decimals otherwise."""
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import SystemSetting

Number = int | float

# key -> (default, minimum, maximum). Later increments add their keys.
SPECS: dict[str, tuple[Number, Number, Number]] = {
    "auth.email_link_hours": (72, 1, 720),
    "auth.reset_link_minutes": (60, 5, 1440),
    "auth.idle_timeout_minutes": (30, 5, 480),
    "auth.session_max_hours": (12, 1, 72),
    "auth.lockout_attempts": (5, 3, 20),
    "auth.lockout_minutes": (15, 1, 1440),
    "auth.password_min_length": (8, 8, 64),
    "auth.registrations_per_ip_hour": (5, 1, 1000),
    "applications.max_active": (5, 1, 20),
    "files.cv_max_mb": (5, 1, 20),
    "files.attachment_max_mb": (10, 1, 50),
    "reports.max_attachments": (3, 1, 10),
    "verification.document_retention_days": (30, 1, 365),
    "files.signed_url_seconds": (60, 10, 3600),
    "attendance.edit_days": (7, 1, 60),
    "attendance.pending_after_days": (3, 0, 30),
    "matching.weight_semantic": (0.5, 0.0, 1.0),
    "matching.weight_required": (0.4, 0.0, 1.0),
    "matching.weight_preferred": (0.1, 0.0, 1.0),
    "matching.semantic_floor": (0.70, 0.0, 0.99),
    "matching.semantic_ceiling": (0.95, 0.01, 1.0),
}


def get(db: Session, key: str) -> Number:
    row = db.get(SystemSetting, key)
    if row is not None:
        return row.value  # type: ignore[return-value]
    return SPECS[key][0]


def all_values(db: Session) -> dict[str, Number]:
    rows = {r.key: r.value for r in db.query(SystemSetting).all()}
    return {k: rows.get(k, spec[0]) for k, spec in SPECS.items()}


def validate(values: dict) -> dict[str, Number]:
    errors, clean = [], {}
    for key, value in values.items():
        spec = SPECS.get(key)
        if spec is None:
            errors.append({"field": key, "code": "UNKNOWN_SETTING", "message": "Unknown setting"})
            continue
        whole = isinstance(spec[0], int)
        if isinstance(value, float) and whole and value.is_integer():
            value = int(value)
        ok_type = isinstance(value, int) if whole else isinstance(value, int | float)
        if isinstance(value, bool) or not ok_type or not spec[1] <= value <= spec[2]:
            errors.append({"field": key, "code": "OUT_OF_RANGE", "message": f"{spec[1]}–{spec[2]}"})
            continue
        clean[key] = value if whole else float(value)
    if errors:
        raise ApiError(422, "VALIDATION_ERROR", errors=errors)
    return clean
