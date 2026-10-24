"""APScheduler inside the API process (Design 5.3), started only when SCHEDULER_ENABLED=true. The Missing flag
also runs 30 seconds after start, so an API that was asleep or restarted catches up at once (NFR-REL-03)."""
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.clock import RIYADH
from app.core.db import SessionLocal
from app.jobs.jobs import run


def start() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=RIYADH)
    scheduler.add_job(run, IntervalTrigger(minutes=15), args=[SessionLocal, "flag_missing"], id="flag_missing",
                      max_instances=1, coalesce=True, next_run_time=datetime.now(RIYADH) + timedelta(seconds=30))
    scheduler.add_job(run, CronTrigger(hour=3, minute=0), args=[SessionLocal, "purge_verification_documents"],
                      id="purge_verification_documents", max_instances=1, coalesce=True)
    scheduler.add_job(run, CronTrigger(hour=3, minute=30), args=[SessionLocal, "cleanup"], id="cleanup",
                      max_instances=1, coalesce=True)
    scheduler.start()
    return scheduler
