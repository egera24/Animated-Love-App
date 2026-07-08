from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import LlmUsage


class UsageTracker:
    """Tracks daily LLM call counts, isolated per category.

    Rows are stored as ``{category}:{provider}`` so that separate features
    (e.g. daily ``bubble`` vs. interactive ``chat``) each get their own budget
    and never starve one another.
    """

    def __init__(self, db: Session, *, daily_call_limit: int = 50, category: str = "bubble") -> None:
        self._db = db
        self._daily_call_limit = daily_call_limit
        self._category = category

    def _today(self) -> str:
        return date.today().isoformat()

    def _provider_key(self, provider: str) -> str:
        return f"{self._category}:{provider}"

    def total_calls_today(self) -> int:
        day = self._today()
        like = f"{self._category}:%"
        row = self._db.scalar(
            select(func.coalesce(func.sum(LlmUsage.calls), 0)).where(
                LlmUsage.usage_date == day,
                LlmUsage.provider.like(like),
            )
        )
        return int(row or 0)

    def can_call(self) -> bool:
        return self.total_calls_today() < self._daily_call_limit

    def record(self, provider: str, *, calls: int = 1, tokens: int = 0) -> None:
        day = self._today()
        key = self._provider_key(provider)
        existing = self._db.scalar(
            select(LlmUsage).where(
                LlmUsage.usage_date == day,
                LlmUsage.provider == key,
            )
        )
        if existing:
            existing.calls += calls
            existing.tokens += tokens
        else:
            self._db.add(
                LlmUsage(
                    usage_date=day,
                    provider=key,
                    calls=calls,
                    tokens=tokens,
                )
            )
        self._db.commit()
