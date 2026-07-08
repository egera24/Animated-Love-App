from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.config import load_profile
from app.services.bubble_service import resolve_bubble_text
from app.services.content_modules import (
    _module_enabled,
    generate_module_content,
    get_enabled_modules,
)
from app.services.feeds import FEED_MODULES, generate_feed_digest
from app.services.mood import resolve_mood
from app.services.weather import fetch_weather

logger = logging.getLogger(__name__)


async def run_prefetch(db: Session) -> dict[str, Any]:
    profile = load_profile()
    weather_data = await fetch_weather(profile)
    weather_mood = weather_data.get("mood_hint") if weather_data else None
    mood_result = resolve_mood(profile, weather_mood=weather_mood)

    bubble = await resolve_bubble_text(
        db,
        profile,
        mood_result,
        weather=weather_data,
    )

    modules_done: dict[str, str] = {}
    for module in get_enabled_modules(profile):
        try:
            result = await generate_module_content(db, module, profile)
            modules_done[module] = "ok" if result else "empty"
        except Exception as e:
            logger.exception("Prefetch module %s failed", module)
            modules_done[module] = f"error: {e}"

    modules_cfg = profile.get("modules_enabled", {})
    for module in FEED_MODULES:
        if not _module_enabled(modules_cfg, module):
            continue
        try:
            result = await generate_feed_digest(db, module, profile)
            modules_done[module] = "ok" if result else "empty"
        except Exception as e:
            logger.exception("Prefetch feed %s failed", module)
            modules_done[module] = f"error: {e}"

    return {
        "ok": True,
        "mood": mood_result.mood,
        "bubble_cached": bool(bubble.text),
        "modules": modules_done,
    }
