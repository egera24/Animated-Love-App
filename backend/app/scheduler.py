from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings, load_profile
from app.db.session import SessionLocal
from app.services.prefetch import run_prefetch

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _prefetch_job() -> None:
    db = SessionLocal()
    try:
        result = await run_prefetch(db)
        logger.info("Scheduled prefetch completed: %s", result)
    except Exception:
        logger.exception("Scheduled prefetch failed")
    finally:
        db.close()


def start_scheduler() -> AsyncIOScheduler | None:
    global _scheduler
    settings = get_settings()
    if not settings.enable_scheduler:
        logger.info("APScheduler disabled (ENABLE_SCHEDULER=false)")
        return None

    profile = load_profile()
    tz_name = profile.get("locations", {}).get("timezone", "Europe/Budapest")
    tz = ZoneInfo(tz_name)

    _scheduler = AsyncIOScheduler(timezone=tz)
    _scheduler.add_job(
        _prefetch_job,
        CronTrigger(hour=6, minute=0, timezone=tz),
        id="daily_prefetch",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("APScheduler started — daily prefetch at 06:00 %s", tz_name)
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
