"""Similarity detection between reports of one university (FR-SIM-01 – 03; Design 6.3; Increment 3 design, Section 4).

The check is created with the submission and run right after it, in the background; `retry` (a scheduled job) runs
the ones still pending or failed. A flag is advisory: nothing here changes a report status or a grade."""
import logging
import uuid
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from app.ai import embeddings
from app.ai.embeddings import QUERY
from app.core import audit, clock, settings
from app.core.deps import Actor
from app.core.errors import ApiError, conflict, forbidden
from app.models import (
    College,
    Placement,
    ReportPassage,
    ReportSlot,
    ReportVersion,
    SimilarityCheck,
    SimilarityMatch,
    StudentProfile,
    TrainingCycle,
    User,
)
from app.similarity.passages import Candidate, overlap, split

log = logging.getLogger("internsync.similarity")
NEIGHBOURS = 5
TOP_SOURCES = 5
MAX_ATTEMPTS = 3


def create_check(db: Session, version: ReportVersion) -> SimilarityCheck:
    c = SimilarityCheck(version_id=version.id, threshold=Decimal(str(settings.get(db, "similarity.threshold"))))
    db.add(c)
    db.flush()
    return c


def _context(db: Session, version: ReportVersion) -> tuple[ReportSlot, Placement, User, uuid.UUID]:
    slot = db.get(ReportSlot, version.slot_id)
    placement = db.get(Placement, slot.placement_id)
    student = db.get(User, placement.student_id)
    return slot, placement, student, db.get(College, student.college_id).university_id


def check(db: Session, check_id: uuid.UUID) -> SimilarityCheck:
    """Compare one submitted version with the stored passages of its university, then store its own passages."""
    c = db.get(SimilarityCheck, check_id)
    version = db.get(ReportVersion, c.version_id)
    slot, _, _, university = _context(db, version)
    c.attempts, c.started_at = c.attempts + 1, clock.now()
    embedder = embeddings.get_embedder()
    if embedder is None:
        c.status, c.error = "failed", "embedding model not available"
        return c
    body = version.body_text or ""
    parts = split(body)
    vectors = embedder.encode([QUERY + p.text for p in parts]) if parts else []
    cos_min = settings.get(db, "similarity.passage_cosine")
    n = settings.get(db, "similarity.ngram_size")
    share = settings.get(db, "similarity.ngram_containment")
    db.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))  # the university filter never empties the result
    candidates = []
    for vector in vectors:
        distance = ReportPassage.embedding.cosine_distance(vector)
        rows = db.execute(select(ReportPassage.version_id, ReportPassage.char_start, ReportPassage.char_end,
                                 ReportPassage.text, (1 - distance).label("cosine"))
                          .where(ReportPassage.university_id == university, ReportPassage.slot_id != slot.id)
                          .order_by(distance).limit(NEIGHBOURS)).all()
        candidates.append([Candidate(r.version_id, r.char_start, r.char_end, r.text, r.cosine) for r in rows])
    scores = overlap(body, parts, candidates, cos_min, n, share, TOP_SOURCES)
    db.query(SimilarityMatch).filter(SimilarityMatch.check_id == c.id).delete()
    for score, vid, pairs in scores:
        db.add(SimilarityMatch(check_id=c.id, source_version_id=vid, score=Decimal(f"{score:.4f}"), passages=pairs))
    best = Decimal(f"{scores[0][0]:.4f}") if scores else Decimal(0)
    c.max_score, c.is_flagged = best, best >= c.threshold
    c.status, c.error, c.finished_at, c.model_version = "done", None, clock.now(), embedder.version
    db.query(ReportPassage).filter(ReportPassage.version_id == version.id).delete()
    db.add_all([ReportPassage(version_id=version.id, slot_id=slot.id, university_id=university, idx=i,
                              char_start=p.start, char_end=p.end, text=p.text, embedding=vector)
                for i, (p, vector) in enumerate(zip(parts, vectors, strict=True))])
    return c


def run_in_background(check_id: uuid.UUID) -> None:
    """Run one check in its own session, after the submission was answered (Increment 3 design, RQ-2)."""
    from app.core.db import SessionLocal

    with SessionLocal() as db:
        try:
            check(db, check_id)
            db.commit()
        except Exception:  # the retry job runs it again
            db.rollback()
            log.exception("similarity check %s failed", check_id)
            c = db.get(SimilarityCheck, check_id)
            if c is not None:
                c.status, c.attempts, c.error = "failed", c.attempts + 1, "unexpected error"
                db.commit()


def retry(db: Session) -> int:
    """Checks still pending 5 minutes after the submission, and failed ones with attempts left."""
    stale = clock.now() - timedelta(minutes=5)
    rows = db.scalars(select(SimilarityCheck.id).where(or_(
        (SimilarityCheck.status == "pending") & (SimilarityCheck.created_at < stale),
        (SimilarityCheck.status == "failed") & (SimilarityCheck.attempts < MAX_ATTEMPTS)))
        .order_by(SimilarityCheck.created_at).limit(50)).all()
    for check_id in rows:
        with db.begin_nested():
            check(db, check_id)
    return len(rows)


# ---------------------------------------------------------------- reading and the decision
def _relation(db: Session, actor: Actor, placement: Placement) -> str:
    if actor.code == "as" and placement.academic_supervisor_id == actor.id:
        return "as"
    if actor.code == "co" and db.get(User, placement.student_id).college_id == actor.user.college_id:
        return "co"
    raise forbidden()


def _report_ref(db: Session, version: ReportVersion) -> dict:
    slot = db.get(ReportSlot, version.slot_id)
    placement = db.get(Placement, slot.placement_id)
    cycle = db.get(TrainingCycle, placement.cycle_id)
    return {"version_id": version.id, "slot_id": slot.id, "kind": slot.kind, "week_no": slot.week_no,
            "version_no": version.version_no, "cycle_id": cycle.id, "cycle_name": cycle.name}


def result(db: Session, actor: Actor, version: ReportVersion) -> dict:
    slot = db.get(ReportSlot, version.slot_id)
    placement = db.get(Placement, slot.placement_id)
    relation = _relation(db, actor, placement)
    c = db.scalar(select(SimilarityCheck).where(SimilarityCheck.version_id == version.id))
    if c is None:
        return {"status": "none", "advisory": True, "sources": [], "can_decide": False}
    body = version.body_text or ""
    sources = []
    for m in db.scalars(select(SimilarityMatch).where(SimilarityMatch.check_id == c.id)
                        .order_by(SimilarityMatch.score.desc())):
        source = db.get(ReportVersion, m.source_version_id)
        ref = _report_ref(db, source)
        author = None
        source_placement = db.get(Placement, db.get(ReportSlot, source.slot_id).placement_id)
        source_student = db.get(User, source_placement.student_id)
        if actor.code == "co" and source_student.college_id == actor.user.college_id:  # FR-SIM-02
            profile = db.get(StudentProfile, source_student.id)
            author = {"id": source_student.id, "name_en": source_student.name_en, "name_ar": source_student.name_ar,
                      "student_number": profile.student_number if profile else None}
        source_body = source.body_text or ""
        sources.append({**ref, "score": m.score, "author": author, "passages": [
            {**pair, "report_text": body[pair["report"][0]:pair["report"][1]],
             "source_text": source_body[pair["source"][0]:pair["source"][1]]} for pair in m.passages]})
    decider = db.get(User, c.decided_by) if c.decided_by else None
    decided_by = {"decided_by_en": decider.name_en, "decided_by_ar": decider.name_ar} if decider else {}
    return {"status": c.status, "max_score": c.max_score, "is_flagged": c.is_flagged, "threshold": c.threshold,
            "model_version": c.model_version, "checked_at": c.finished_at, "error": c.error, "advisory": True,
            "decision": c.decision, "decision_comment": c.decision_comment, "decided_at": c.decided_at,
            **decided_by, "can_decide": relation == "as" and c.status == "done" and c.is_flagged, "sources": sources}


def decide(db: Session, actor: Actor, version: ReportVersion, decision: str, comment: str) -> None:
    """FR-SIM-03: the assigned supervisor's advisory decision on a flagged check; nothing else changes."""
    slot = db.get(ReportSlot, version.slot_id)
    placement = db.get(Placement, slot.placement_id)
    if actor.code != "as" or placement.academic_supervisor_id != actor.id:
        raise forbidden()
    c = db.scalar(select(SimilarityCheck).where(SimilarityCheck.version_id == version.id))
    if c is None or c.status != "done" or not c.is_flagged:
        raise conflict("NOT_FLAGGED")
    if not comment.strip():
        raise ApiError(422, "COMMENT_REQUIRED")
    old = c.decision
    c.decision, c.decision_comment, c.decided_by, c.decided_at = decision, comment.strip(), actor.id, clock.now()
    student = db.get(User, placement.student_id)
    audit.record(db, actor.user, "similarity_decision", "report_slot", slot.id, student_id=student.id,
                 college_id=student.college_id, cycle_id=placement.cycle_id, old={"decision": old},
                 new={"decision": decision, "version_no": version.version_no}, reason=c.decision_comment)


def listing(db: Session, actor: Actor, cycle_id: uuid.UUID | None, flagged: bool | None,
            decided: bool | None) -> list[dict]:
    stmt = (select(SimilarityCheck, ReportVersion, ReportSlot, Placement, User)
            .join(ReportVersion, ReportVersion.id == SimilarityCheck.version_id)
            .join(ReportSlot, ReportSlot.id == ReportVersion.slot_id)
            .join(Placement, Placement.id == ReportSlot.placement_id)
            .join(User, User.id == Placement.student_id))
    if actor.code == "as":
        stmt = stmt.where(Placement.academic_supervisor_id == actor.id)
    else:
        stmt = stmt.where(User.college_id == actor.user.college_id)
    if cycle_id:
        stmt = stmt.where(Placement.cycle_id == cycle_id)
    if flagged is not None:
        stmt = stmt.where(SimilarityCheck.is_flagged.is_(flagged))
    if decided is not None:
        stmt = stmt.where(SimilarityCheck.decision.is_not(None) if decided else SimilarityCheck.decision.is_(None))
    out = []
    for c, v, slot, p, student in db.execute(stmt.order_by(SimilarityCheck.created_at.desc()).limit(200)):
        out.append({"check_id": c.id, "version_id": v.id, "slot_id": slot.id, "placement_id": p.id,
                    "kind": slot.kind, "week_no": slot.week_no, "version_no": v.version_no,
                    "student": {"id": student.id, "name_en": student.name_en, "name_ar": student.name_ar},
                    "status": c.status, "max_score": c.max_score, "is_flagged": c.is_flagged,
                    "decision": c.decision, "checked_at": c.finished_at})
    return out
