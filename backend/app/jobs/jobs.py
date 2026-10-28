"""Scheduled jobs (Design 5.3; Increment 1 design, Section 7; Increment 3 design, Section 5). They select work by
state, not by time window, so a run missed during downtime catches up on the next one (NFR-REL-03)."""
import logging
from collections.abc import Callable
from datetime import timedelta

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.core import audit, clock, files, settings
from app.matching.service import embed_missing
from app.models import (
    AccountToken,
    JobRun,
    Placement,
    ReportSlot,
    ReportVersion,
    StoredFile,
    User,
    UserSession,
    VerificationDocument,
    VerificationRequest,
)
from app.notifications import delivery, scheduled
from app.similarity.service import retry as similarity_retry

log = logging.getLogger("internsync.jobs")
LOCK_IDS = {"flag_missing": 7101, "purge_verification_documents": 7102, "cleanup": 7103, "embed_missing": 7104,
            "send_reminders": 7105, "escalate_overdue": 7106, "deliver_notifications": 7107,
            "similarity_retry": 7108}


def flag_missing(db: Session) -> int:
    """FR-REP-04: slots still in draft after their deadline are flagged Missing; the student and the academic
    supervisor are told (FR-NOT-03)."""
    now = clock.now()
    submitted = select(ReportVersion.id).where(ReportVersion.slot_id == ReportSlot.id,
                                               ReportVersion.submitted_at.is_not(None))
    slots = db.scalars(select(ReportSlot).join(Placement, Placement.id == ReportSlot.placement_id)
                       .where(ReportSlot.status == "draft", ReportSlot.due_at < now, ReportSlot.is_missing.is_(False),
                              Placement.status == "active", ~submitted.exists())).all()
    for slot in slots:
        slot.is_missing, slot.missing_flagged_at = True, now
        placement = db.get(Placement, slot.placement_id)
        student = db.get(User, placement.student_id)
        audit.record(db, None, "flag_missing", "report_slot", slot.id, student_id=student.id,
                     college_id=student.college_id, cycle_id=placement.cycle_id, new={"is_missing": True})
        scheduled.report_missing(db, slot, placement)
    return len(slots)


def purge_verification_documents(db: Session) -> int:
    """FR-ORG-08: documents are deleted from storage N days after the decision; the decision stays."""
    cutoff = clock.now() - timedelta(days=settings.get(db, "verification.document_retention_days"))
    docs = db.execute(select(VerificationDocument, StoredFile)
                      .join(VerificationRequest, VerificationRequest.id == VerificationDocument.request_id)
                      .join(StoredFile, StoredFile.id == VerificationDocument.file_id)
                      .where(VerificationRequest.decided_at.is_not(None), VerificationRequest.decided_at < cutoff,
                             VerificationDocument.purged_at.is_(None))).all()
    store = files.storage()
    for doc, f in docs:
        store.delete(f.storage_key)
        doc.purged_at = clock.now()
    return len(docs)


def cleanup(db: Session) -> int:
    now = clock.now()
    n = db.execute(delete(UserSession).where((UserSession.expires_at < now - timedelta(days=1))
                                             | (UserSession.revoked_at < now - timedelta(days=1)))).rowcount
    n += db.execute(delete(AccountToken).where(AccountToken.expires_at < now - timedelta(days=30))).rowcount
    n += db.execute(delete(JobRun).where(JobRun.started_at < now - timedelta(days=30))).rowcount
    return n


JOBS: dict[str, Callable[[Session], int]] = {"flag_missing": flag_missing,
                                             "purge_verification_documents": purge_verification_documents,
                                             "cleanup": cleanup, "embed_missing": embed_missing,
                                             "send_reminders": scheduled.send_reminders,
                                             "escalate_overdue": scheduled.escalate_overdue,
                                             "deliver_notifications": delivery.deliver,
                                             "similarity_retry": similarity_retry}


def run(db_factory, name: str) -> None:
    """Run one job in a single transaction under a transaction-level PostgreSQL advisory lock and record it in
    job_runs. The lock ends with the transaction, so a failed or crashed run never leaves it held, and a second
    instance that cannot take it skips the run."""
    db: Session = db_factory()
    try:
        if not db.scalar(text("SELECT pg_try_advisory_xact_lock(:id)"), {"id": LOCK_IDS[name]}):
            db.rollback()
            return
        started = clock.now()
        try:
            items = JOBS[name](db)
            db.add(JobRun(job_name=name, started_at=started, finished_at=clock.now(), status="ok", items=items))
            db.commit()
        except Exception as exc:  # recorded, retried on the next run
            db.rollback()
            log.exception("job %s failed", name)
            db.add(JobRun(job_name=name, started_at=started, finished_at=clock.now(), status="error",
                          error=str(exc)[:2000]))
            db.commit()
    finally:
        db.close()
