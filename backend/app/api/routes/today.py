from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.deps import require_auth
from app.api.schemas import (
    BubbleRefreshResponse,
    ContentSnippet,
    LinkItem,
    TodayResponse,
    WeatherInfo,
)
from app.config import load_profile
from app.db.session import SessionLocal
from app.services.bubble_service import resolve_bubble_text
from app.services.content_cache import get_cached
from app.services.content_modules import generate_module_content
from app.services.expression import mood_to_expression
from app.services.feeds import FEED_MODULES, generate_feed_digest
from app.services.mood import _today_in_tz, resolve_mood
from app.services.weather import fetch_weather

router = APIRouter(prefix="/api", tags=["today"])

_NO_STORE = {"Cache-Control": "no-store"}


def _snippet(module: str, cached: dict | None) -> ContentSnippet | None:
    if not cached or not cached.get("text"):
        return None
    raw_items = cached.get("items")
    items = None
    if isinstance(raw_items, list) and raw_items:
        items = [
            LinkItem(title=str(i.get("title", "")), url=i.get("url"))
            for i in raw_items
            if isinstance(i, dict) and i.get("title")
        ]
    return ContentSnippet(
        module=module,
        text=str(cached["text"]),
        title=cached.get("title"),
        items=items,
    )


async def _load_module_snippet(db, module: str, profile: dict, content_date: str):
    from app.services.content_modules import _module_enabled

    modules_cfg = profile.get("modules_enabled", {})
    if not _module_enabled(modules_cfg, module):
        return None
    cached = get_cached(db, content_date, module)
    if not cached:
        if module in FEED_MODULES:
            cached = await generate_feed_digest(db, module, profile)
        else:
            cached = await generate_module_content(db, module, profile)
    return _snippet(module, cached)


async def _build_today_response(*, force_refresh_bubble: bool) -> TodayResponse:
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
            force_refresh=force_refresh_bubble,
        )
        content_date = _today_in_tz(profile).isoformat()
        poem = await _load_module_snippet(db, "poem", profile, content_date)
        book = await _load_module_snippet(db, "book", profile, content_date)
        movie = await _load_module_snippet(db, "movie", profile, content_date)
        news = await _load_module_snippet(db, "news", profile, content_date)
        health = await _load_module_snippet(db, "health", profile, content_date)
    finally:
        db.close()

    hedgehog = profile.get("hedgehog", {})
    recipient = profile.get("recipient", {})
    weather_info = WeatherInfo(**weather_data) if weather_data else None

    return TodayResponse(
        mood=mood_result.mood,
        expression=mood_to_expression(mood_result.mood),
        bubble_text=bubble.text,
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
        news=news,
        health=health,
    )


@router.get("/today")
async def get_today(request: Request):
    require_auth(request)
    data = await _build_today_response(force_refresh_bubble=False)
    return JSONResponse(content=data.model_dump(), headers=_NO_STORE)


@router.post("/today/bubble/refresh", response_model=BubbleRefreshResponse)
async def refresh_bubble(request: Request):
    """New bubble on each call (Fahéj tap). POST avoids browser GET caching."""
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
            force_refresh=True,
        )
    finally:
        db.close()

    return BubbleRefreshResponse(
        bubble_text=bubble.text,
        mood=mood_result.mood,
        expression=mood_to_expression(mood_result.mood),
        bubble_source=bubble.source,
    )
