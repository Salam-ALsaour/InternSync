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

__all__ = ["normalize", "extract", "find", "refresh_index", "Match"]
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


CONJUNCTIONS = ("و", "ف")
PREPOSITIONS = ("ب", "ل", "ك")


def variants(token: str) -> list[str]:
    """The token and the forms without an attached Arabic conjunction or preposition (و، ف، ب، ل، ك), as in
    «والتواصل» or «بالتعلم». A variant is used only when it completes a known phrase, so ordinary words stay."""
    out = [token]
    for t in list(out):
        if t[:1] in CONJUNCTIONS and len(t) > 3:
            out.append(t[1:])
    for t in list(out):
        if t.startswith("لل") and len(t) > 4:
            out.append("ال" + t[2:])
        elif t[:1] in PREPOSITIONS and len(t) > 3:
            out.append(t[1:])
    return list(dict.fromkeys(out))


def find(index: dict, text: str) -> dict:
    """Scan the normalized tokens of `text` with phrases of 1 to MAX_N tokens; the longest phrase in `index`
    wins at each position, and the first token may drop an attached Arabic particle (see variants). Returns
    {value: token context} for each value of `index` that was found."""
    toks = tokens(text)
    found: dict = {}
    i = 0
    while i < len(toks):
        for n in range(min(MAX_N, len(toks) - i), 0, -1):
            rest = toks[i + 1:i + n]
            value = next((index[k] for k in (" ".join([first, *rest]) for first in variants(toks[i])) if k in index),
                         None)
            if value is not None:
                found.setdefault(value, " ".join(toks[max(0, i - 6):i + n + 6]))
                i += n
                break
        else:
            i += 1
    return found


def extract(db: Session, text: str) -> list[Match]:
    _ensure_index(db)
    return [Match(skill_id=sid, evidence=_evidence(text, sid, fb)[:120]) for sid, fb in find(_index, text).items()]
