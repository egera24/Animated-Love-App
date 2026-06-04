from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import LlmUsage


class UsageTracker:
    def __init__(self, db: Session, *, daily_call_limit: int = 50) -> None:
        self._db = db
        self._daily_call_limit = daily_call_limit

    def _today(self) -> str:
        return date.today().isoformat()

    def total_calls_today(self) -> int:
        day = self._today()
        row = self._db.scalar(
            select(func.coalesce(func.sum(LlmUsage.calls), 0)).where(LlmUsage.usage_date == day)
        )
        return int(row or 0)

    def can_call(self) -> bool:
        return self.total_calls_today() < self._daily_call_limit

    def record(self, provider: str, *, calls: int = 1, tokens: int = 0) -> None:
        day = self._today()
        existing = self._db.scalar(
            select(LlmUsage).where(
                LlmUsage.usage_date == day,
                LlmUsage.provider == provider,
            )
        )
        if existing:
            existing.calls += calls
            existing.tokens += tokens
        else:
            self._db.add(
                LlmUsage(
                    usage_date=day,
                    provider=provider,
                    calls=calls,
                    tokens=tokens,
                )
            )
        self._db.commit()
