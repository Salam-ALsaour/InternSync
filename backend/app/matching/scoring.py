"""The fit score as pure functions (Design 6.2, FR-MAT-02, FR-MAT-04, FR-MAT-05). No database, so the AI
evaluation script and the unit tests use exactly the code the API uses."""
from collections.abc import Collection, Hashable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Weights:
    semantic: float = 0.5
    required: float = 0.4
    preferred: float = 0.1
    floor: float = 0.70
    ceiling: float = 0.95


@dataclass
class Fit:
    score: float
    mode: str  # "semantic" or "basic" (FR-MAT-04)
    semantic: float | None
    required: float
    preferred: float | None  # None when the vacancy lists no preferred skill
    matched: list = field(default_factory=list)
    missing: list = field(default_factory=list)


def semantic_part(cosine: float, w: Weights) -> float:
    """Spread the narrow cosine range of the e5 models over 0–1 (floor and ceiling are settings)."""
    span = max(w.ceiling - w.floor, 1e-6)
    return min(1.0, max(0.0, (cosine - w.floor) / span))


def score(student_skills: Collection[Hashable], required: Collection[Hashable], preferred: Collection[Hashable],
          cosine: float | None, w: Weights) -> Fit:
    """`cosine` is None when either text has no embedding or the model is off: the rule-based score is used."""
    s, r, p = set(student_skills), set(required), set(preferred)
    required_part = len(s & r) / len(r) if r else 1.0
    preferred_part = len(s & p) / len(p) if p else None
    pref = preferred_part or 0.0
    w_required, w_preferred = w.required, w.preferred
    if not p:  # no preferred skills: their weight moves to the required part
        w_required, w_preferred = w.required + w.preferred, 0.0
    matched = sorted(s & r, key=str)
    missing = sorted(r - s, key=str)
    if cosine is None:
        rules = w_required + w_preferred
        value = (w_required * required_part + w_preferred * pref) / rules if rules else required_part
        return Fit(round(100 * value, 2), "basic", None, required_part, preferred_part, matched, missing)
    sem = semantic_part(cosine, w)
    total = w.semantic + w_required + w_preferred
    value = (w.semantic * sem + w_required * required_part + w_preferred * pref) / total if total else 0.0
    return Fit(round(100 * value, 2), "semantic", sem, required_part, preferred_part, matched, missing)
