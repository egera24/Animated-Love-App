from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings, load_profile
from app.services.content_cache import get_cached, set_cached
from app.services.fallbacks import build_bubble_text
from app.services.llm.router import generate_bubble
from app.services.mood import MoodResult


@dataclass
class BubbleResult:
    text: str
    source: str


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
) -> BubbleResult:
    content_date = _today_key(profile)
    cached = get_cached(db, content_date, "bubble")
    if not force_refresh and cached and cached.get("bubble_text"):
        if cached.get("source") != "static" or not get_settings().has_any_llm_key():
            return BubbleResult(
                text=str(cached["bubble_text"]),
                source=str(cached.get("source", "cache")),
            )

    context = {
        "is_birthday": mood_result.is_birthday,
        "special_date_label": mood_result.special_date_label,
        "behavior": mood_result.behavior,
        "topic_hints": mood_result.topic_hints,
        "weather": weather,
        "interactive_refresh": force_refresh,
        "previous_bubble": (
            str(cached.get("bubble_text"))
            if force_refresh and cached and cached.get("bubble_text")
            else None
        ),
        "variation_id": secrets.token_hex(4) if force_refresh else None,
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
        return BubbleResult(text=llm.bubble_text, source="llm")

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
        return BubbleResult(text=text, source="static")
    return BubbleResult(text=text, source="static_ephemeral")
