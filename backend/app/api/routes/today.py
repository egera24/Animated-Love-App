from fastapi import APIRouter, Request

from app.api.deps import require_auth
from app.api.schemas import ContentSnippet, TodayResponse, WeatherInfo
from app.config import load_profile
from app.debug_log import dbg
from app.services.content_cache import get_cached
from app.services.mood import _today_in_tz
from app.db.session import SessionLocal
from app.services.bubble_service import resolve_bubble_text
from app.services.content_modules import generate_module_content
from app.services.mood import resolve_mood
from app.services.weather import fetch_weather

router = APIRouter(prefix="/api", tags=["today"])


def _snippet(module: str, cached: dict | None) -> ContentSnippet | None:
    if not cached or not cached.get("text"):
        return None
    return ContentSnippet(
        module=module,
        text=str(cached["text"]),
        title=cached.get("title"),
    )


async def _load_module_snippet(db, module: str, profile: dict, content_date: str):
    from app.services.content_modules import _module_enabled

    modules_cfg = profile.get("modules_enabled", {})
    if not _module_enabled(modules_cfg, module):
        return None
    cached = get_cached(db, content_date, module)
    if not cached:
        cached = await generate_module_content(db, module, profile)
    return _snippet(module, cached)


@router.get("/today", response_model=TodayResponse)
async def get_today(request: Request):
    require_auth(request)
    profile = load_profile()
    weather_data = await fetch_weather(profile)
    weather_mood = weather_data.get("mood_hint") if weather_data else None

    mood_result = resolve_mood(profile, weather_mood=weather_mood)

    db = SessionLocal()
    try:
        bubble = await resolve_bubble_text(
            db,
            profile,
            mood_result,
            weather=weather_data,
        )
        content_date = _today_in_tz(profile).isoformat()
        after_cache = get_cached(db, content_date, "bubble")
        # #region agent log
        dbg(
            "D",
            "today.py:get_today",
            "response_bubble",
            {
                "bubble_len": len(bubble),
                "bubble_prefix": bubble[:40],
                "final_source": after_cache.get("source") if after_cache else None,
            },
        )
        # #endregion
        poem = await _load_module_snippet(db, "poem", profile, content_date)
        book = await _load_module_snippet(db, "book", profile, content_date)
        movie = await _load_module_snippet(db, "movie", profile, content_date)
    finally:
        db.close()

    hedgehog = profile.get("hedgehog", {})
    recipient = profile.get("recipient", {})

    weather_info = None
    if weather_data:
        weather_info = WeatherInfo(**weather_data)

    return TodayResponse(
        mood=mood_result.mood,
        bubble_text=bubble,
        hedgehog_name=hedgehog.get("name", "Fahéj"),
        recipient_name=recipient.get("name", "Edina"),
        is_birthday=mood_result.is_birthday,
        is_special_date=mood_result.is_special_date,
        special_date_label=mood_result.special_date_label,
        weather=weather_info,
        language=profile.get("content", {}).get("default_language", "hu"),
        poem=poem,
        book_tip=book,
        movie_tip=movie,
    )
