from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings, load_profile
from app.services.content_cache import get_cached, set_cached
from app.services.fallbacks import build_bubble_text
from app.services.llm.router import generate_bubble
from app.services.mood import MoodResult


def _today_key(profile: dict[str, Any]) -> str:
    from app.services.mood import _today_in_tz

    return _today_in_tz(profile).isoformat()


async def resolve_bubble_text(
    db: Session,
    profile: dict[str, Any],
    mood_result: MoodResult,
    *,
    weather: dict[str, Any] | None,
    force_refresh: bool = False,
) -> str:
    content_date = _today_key(profile)
    cached = get_cached(db, content_date, "bubble")
    if not force_refresh and cached and cached.get("bubble_text"):
        # Stale static cache blocks LLM after a single failed provider call — retry when keys exist.
        if cached.get("source") != "static" or not get_settings().has_any_llm_key():
            return str(cached["bubble_text"])

    context = {
        "is_birthday": mood_result.is_birthday,
        "special_date_label": mood_result.special_date_label,
        "weather": weather,
        "interactive_refresh": force_refresh,
    }

    llm = await generate_bubble(
        db,
        mood=mood_result.mood,
        profile=profile,
        context=context,
    )
    if llm:
        payload = {
            "bubble_text": llm.bubble_text,
            "mood": llm.mood,
            "language": llm.language,
            "source": "llm",
        }
        set_cached(db, content_date, "bubble", payload)
        return llm.bubble_text

    text = build_bubble_text(
        profile,
        mood_result.mood,
        is_birthday=mood_result.is_birthday,
        special_label=mood_result.special_date_label,
        weather=weather,
    )
    if not get_settings().has_any_llm_key():
        set_cached(
            db,
            content_date,
            "bubble",
            {"bubble_text": text, "mood": mood_result.mood, "source": "static"},
        )
    return text
