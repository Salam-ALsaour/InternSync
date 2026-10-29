"""The student's evaluation of the training entity and the job-offer survey (FR-EVL-05, FR-DSH-03; Increment 4
design, Section 5). Only the student and the coordinator of the student's college ever see them."""
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit, clock
from app.core.errors import ApiError, conflict, forbidden
from app.models import Company, CompanyEvaluation, Grade, OutcomeSurvey, Placement, TrainingCycle, User, Vacancy
from app.models.tracking import RATINGS

JOB_OFFER = ("yes", "no", "pending")


def opens_on(db: Session, p: Placement) -> date:
    return db.get(Vacancy, p.vacancy_id).training_end


def is_open(db: Session, p: Placement) -> bool:
    """RQ-3: from the training end date (Riyadh) or the Final grade, whichever comes first; never when cancelled."""
    if p.status == "cancelled":
        return False
    if p.status == "completed" or db.scalar(select(Grade.status).where(Grade.placement_id == p.id)) == "final":
        return True
    return clock.now().astimezone(clock.RIYADH).date() >= opens_on(db, p)


def _evaluation_out(e: CompanyEvaluation | None) -> dict | None:
    if e is None:
        return None
    return {**{r: getattr(e, r) for r in RATINGS}, "would_recommend": e.would_recommend, "comment": e.comment,
            "submitted_at": e.submitted_at}


def _survey_out(s: OutcomeSurvey | None) -> dict | None:
    return None if s is None else {"job_offer": s.job_offer, "submitted_at": s.submitted_at, "updated_at": s.updated_at}


def view(db: Session, p: Placement, relation: str) -> dict:
    if relation not in ("st", "co"):
        raise forbidden()
    e, s, open_ = db.get(CompanyEvaluation, p.id), db.get(OutcomeSurvey, p.id), is_open(db, p)
    v = db.get(Vacancy, p.vacancy_id)
    return {"placement_id": p.id, "company": db.get(Company, v.company_id).name, "vacancy": v.title,
            "open_from": opens_on(db, p), "is_open": open_, "evaluation": _evaluation_out(e),
            "survey": _survey_out(s), "can_evaluate": relation == "st" and open_ and e is None,
            "can_answer": relation == "st" and open_}


def _student_only(actor_id, p: Placement) -> None:
    if p.student_id != actor_id:
        raise forbidden()


def _audit(db: Session, actor_user: User, action: str, entity: str, p: Placement, **kw) -> None:
    audit.record(db, actor_user, action, entity, p.id, student_id=p.student_id, college_id=actor_user.college_id,
                 cycle_id=p.cycle_id, **kw)


def evaluate(db: Session, actor_user: User, p: Placement, data: dict) -> None:
    """FR-EVL-05: once, after the placement has ended."""
    _student_only(actor_user.id, p)
    if not is_open(db, p):
        raise conflict("FEEDBACK_NOT_OPEN")
    if db.get(CompanyEvaluation, p.id) is not None:
        raise conflict("ALREADY_SUBMITTED")
    comment = (data.get("comment") or "").strip() or None
    db.add(CompanyEvaluation(placement_id=p.id, **{r: data[r] for r in RATINGS},
                             would_recommend=data["would_recommend"], comment=comment, submitted_at=clock.now()))
    _audit(db, actor_user, "submit", "company_evaluation", p,
           new={**{r: data[r] for r in RATINGS}, "would_recommend": data["would_recommend"]})


def answer(db: Session, actor_user: User, p: Placement, job_offer: str) -> None:
    """FR-DSH-03: the answer may change later, for example from Pending to Yes."""
    _student_only(actor_user.id, p)
    if not is_open(db, p):
        raise conflict("FEEDBACK_NOT_OPEN")
    if job_offer not in JOB_OFFER:
        raise ApiError(422, "VALIDATION_ERROR")
    s = db.get(OutcomeSurvey, p.id)
    old = s.job_offer if s else None
    if s is None:
        db.add(OutcomeSurvey(placement_id=p.id, job_offer=job_offer, submitted_at=clock.now()))
    else:
        s.job_offer = job_offer
    _audit(db, actor_user, "submit" if old is None else "update", "outcome_survey", p,
           old={"job_offer": old} if old else None, new={"job_offer": job_offer})


def due(db: Session, student_id) -> int:
    """Ended placements of the student with a missing evaluation or survey answer (dashboard `feedback_due`)."""
    n = 0
    for p in db.scalars(select(Placement).where(Placement.student_id == student_id, Placement.status != "cancelled")):
        if is_open(db, p) and (db.get(CompanyEvaluation, p.id) is None or db.get(OutcomeSurvey, p.id) is None):
            n += 1
    return n


# ---------------------------------------------------------------- coordinator figures
def _mean(values: list[int]) -> Decimal | None:
    if not values:
        return None
    return (Decimal(sum(values)) / Decimal(len(values))).quantize(Decimal("0.01"), ROUND_HALF_UP)


def _rate(part: int, whole: int) -> float | None:
    return round(100 * part / whole, 1) if whole else None


def _by_company(db: Session, cycle: TrainingCycle, model):
    rows = db.execute(select(model, Vacancy.company_id).join(Placement, Placement.id == model.placement_id)
                      .join(Vacancy, Vacancy.id == Placement.vacancy_id)
                      .where(Placement.cycle_id == cycle.id, Placement.status != "cancelled")).all()
    groups: dict = {}
    for row, company_id in rows:
        groups.setdefault(company_id, []).append(row)
    return [row for row, _ in rows], groups


def _evaluation_figures(items: list[CompanyEvaluation]) -> dict:
    return {"answers": len(items), **{r: _mean([getattr(e, r) for e in items]) for r in RATINGS},
            "recommend_rate": _rate(sum(e.would_recommend for e in items), len(items))}


def company_evaluations(db: Session, cycle: TrainingCycle) -> dict:
    """Averages per company and for the cycle (API 3.12)."""
    everything, groups = _by_company(db, cycle, CompanyEvaluation)
    companies = [{"company_id": cid, "company_name": db.get(Company, cid).name, **_evaluation_figures(items)}
                 for cid, items in groups.items()]
    return {"cycle_id": cycle.id, "overall": _evaluation_figures(everything),
            "companies": sorted(companies, key=lambda c: c["company_name"])}


def _outcome_figures(items: list[OutcomeSurvey]) -> dict:
    yes = sum(s.job_offer == "yes" for s in items)
    return {"answers": len(items), "yes": yes, "no": sum(s.job_offer == "no" for s in items),
            "pending": sum(s.job_offer == "pending" for s in items), "job_offer_rate": _rate(yes, len(items))}


def outcomes(db: Session, cycle: TrainingCycle) -> dict:
    """FR-DSH-03: Yes answers ÷ answers, per cycle and per company; students who did not answer are not counted."""
    everything, groups = _by_company(db, cycle, OutcomeSurvey)
    companies = [{"company_id": cid, "company_name": db.get(Company, cid).name, **_outcome_figures(items)}
                 for cid, items in groups.items()]
    return {"cycle_id": cycle.id, "overall": _outcome_figures(everything),
            "companies": sorted(companies, key=lambda c: c["company_name"])}
