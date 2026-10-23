"""Rule-based skill extraction (FR-PRF-04, Design 6.1; implementation note in Increment 1 design, Section 8).

Every skill name and synonym is normalized into `match_terms`. A CV's normalized tokens are scanned with a
dictionary of 1- to 4-token phrases; the longest phrase wins at each position. The student always confirms."""
import re
import threading
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.text import normalize, tokens
from app.models import Skill

__all__ = ["normalize", "extract", "refresh_index", "Match"]
MAX_N = 4


@dataclass
class Match:
    skill_id: uuid.UUID
    evidence: str


_lock = threading.Lock()
_index: dict[str, uuid.UUID] = {}
_surfaces: dict[uuid.UUID, list[str]] = {}
_signature: tuple | None = None


def refresh_index() -> None:
    global _signature
    with _lock:
        _signature = None


def _ensure_index(db: Session) -> None:
    global _index, _surfaces, _signature
    sig = tuple(db.execute(select(func.count(Skill.id), func.max(Skill.updated_at))).one())
    if sig == _signature:
        return
    index, surfaces = {}, {}
    for skill in db.scalars(select(Skill).where(Skill.is_active).order_by(Skill.name_en)):
        for term in skill.match_terms:
            index.setdefault(term, skill.id)
        surfaces[skill.id] = [skill.name_en, skill.name_ar, *skill.synonyms]
    with _lock:
        _index, _surfaces, _signature = index, surfaces, sig


def _evidence(text: str, skill_id: uuid.UUID, fallback: str) -> str:
    for surface in sorted(_surfaces.get(skill_id, []), key=len, reverse=True):
        if not surface:
            continue
        m = re.search(r"(?<![\w])" + re.escape(surface) + r"(?![\w])", text, flags=re.IGNORECASE)
        if m:
            start, end = max(0, m.start() - 50), min(len(text), m.end() + 50)
            return ("…" if start else "") + " ".join(text[start:end].split()) + ("…" if end < len(text) else "")
    return fallback[:120]


def extract(db: Session, text: str) -> list[Match]:
    _ensure_index(db)
    toks = tokens(text)
    found: dict[uuid.UUID, str] = {}
    i = 0
    while i < len(toks):
        for n in range(min(MAX_N, len(toks) - i), 0, -1):
            phrase = " ".join(toks[i:i + n])
            skill_id = _index.get(phrase)
            if skill_id is not None:
                if skill_id not in found:
                    found[skill_id] = " ".join(toks[max(0, i - 6):i + n + 6])
                i += n
                break
        else:
            i += 1
    return [Match(skill_id=sid, evidence=_evidence(text, sid, fb)[:120]) for sid, fb in found.items()]
