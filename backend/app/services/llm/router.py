from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.debug_log import dbg
from app.services.llm.schemas import BubbleLLMResponse
from app.services.llm.usage import UsageTracker

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Te Fahéj vagy, egy játékos, humoros sün. Edinának írsz rövid, meleg magyar szöveget egy ajándék webapp buborékába.
Első személyben beszélj. Legyél kedves, könnyed humorral — soha ne legyél gúnyos vagy bántó.
Válaszod KIZÁRÓLAG érvényes JSON legyen, más szöveg nélkül:
{"bubble_text": "...", "mood": "...", "language": "hu"}
A mood mező egyezzen a kért hangulattal (ne változtasd meg a naptári logikát)."""


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def _build_user_prompt(
    *,
    mood: str,
    recipient_name: str,
    hedgehog_name: str,
    language: str,
    context: dict[str, Any],
) -> str:
    lines = [
        f"Hangulat (mood): {mood}",
        f"Címzett: {recipient_name}",
        f"Sün neve: {hedgehog_name}",
        f"Nyelv: {language}",
    ]
    if context.get("is_birthday"):
        lines.append("Ma Edina születésnapja — ünnepi hangnem.")
    elif context.get("special_date_label"):
        lines.append(f"Különleges nap: {context['special_date_label']}")
    if weather := context.get("weather"):
        lines.append(
            f"Időjárás ({weather.get('city', 'Szeged')}): "
            f"{weather.get('temp_c')}°C, {weather.get('description_hu', '')}"
        )
    interests = context.get("interests")
    if interests:
        lines.append(f"Érdeklődések (utalhat rájuk finoman): {json.dumps(interests, ensure_ascii=False)}")
    lines.append("Írj 1–3 rövid mondatot a bubble_text mezőbe; időjárást említheted ha releváns.")
    return "\n".join(lines)


async def _call_groq(
    client: httpx.AsyncClient,
    settings: Settings,
    user_prompt: str,
) -> str | None:
    if not settings.groq_api_key:
        return None
    try:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.8,
                "max_tokens": 400,
            },
            timeout=30.0,
        )
        if r.status_code in (401, 403, 429) or r.status_code >= 500:
            logger.warning("Groq HTTP %s", r.status_code)
            return None
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("Groq error: %s", e)
        return None


async def _call_gemini(
    client: httpx.AsyncClient,
    settings: Settings,
    user_prompt: str,
) -> str | None:
    if not settings.gemini_api_key:
        return None
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    try:
        r = await client.post(
            url,
            params={"key": settings.gemini_api_key},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": SYSTEM_PROMPT + "\n\n" + user_prompt},
                        ],
                    }
                ],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 400},
            },
            timeout=30.0,
        )
        if r.status_code in (401, 403, 429) or r.status_code >= 500:
            logger.warning("Gemini HTTP %s", r.status_code)
            return None
        r.raise_for_status()
        data = r.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        if not parts:
            return None
        return parts[0].get("text", "")
    except Exception as e:
        logger.warning("Gemini error: %s", e)
        return None


async def _call_openrouter(
    client: httpx.AsyncClient,
    settings: Settings,
    user_prompt: str,
) -> str | None:
    if not settings.openrouter_api_key:
        return None
    try:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://fahej.local",
                "X-Title": "Fahéj App",
            },
            json={
                "model": settings.openrouter_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.8,
                "max_tokens": 400,
            },
            timeout=45.0,
        )
        if r.status_code in (401, 403, 429) or r.status_code >= 500:
            logger.warning("OpenRouter HTTP %s", r.status_code)
            return None
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("OpenRouter error: %s", e)
        return None


def _parse_bubble(raw: str | None, expected_mood: str) -> BubbleLLMResponse | None:
    if not raw:
        return None
    try:
        data = _extract_json(raw)
        parsed = BubbleLLMResponse.model_validate(data)
        if parsed.mood != expected_mood:
            parsed = parsed.model_copy(update={"mood": expected_mood})
        return parsed
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning("LLM JSON parse failed: %s", e)
        return None


async def generate_bubble(
    db: Session,
    *,
    mood: str,
    profile: dict[str, Any],
    context: dict[str, Any],
) -> BubbleLLMResponse | None:
    settings = get_settings()
    has_keys = settings.has_any_llm_key()
    # #region agent log
    dbg(
        "C",
        "router.py:generate_bubble",
        "entry",
        {
            "has_keys": has_keys,
            "mood": mood,
            "groq_set": bool(settings.groq_api_key and str(settings.groq_api_key).strip()),
            "gemini_set": bool(settings.gemini_api_key and str(settings.gemini_api_key).strip()),
            "openrouter_set": bool(
                settings.openrouter_api_key and str(settings.openrouter_api_key).strip()
            ),
        },
    )
    # #endregion
    if not has_keys:
        return None

    tracker = UsageTracker(db, daily_call_limit=settings.llm_daily_call_limit)
    can_call = tracker.can_call()
    # #region agent log
    dbg(
        "E",
        "router.py:generate_bubble",
        "usage_check",
        {"can_call": can_call, "calls_today": tracker.total_calls_today()},
    )
    # #endregion
    if not can_call:
        logger.info("LLM daily call limit reached")
        return None

    recipient = profile.get("recipient", {}).get("name", "Edina")
    hedgehog = profile.get("hedgehog", {}).get("name", "Fahéj")
    language = profile.get("content", {}).get("default_language", "hu")
    user_prompt = _build_user_prompt(
        mood=mood,
        recipient_name=recipient,
        hedgehog_name=hedgehog,
        language=language,
        context={**context, "interests": profile.get("interests")},
    )

    providers = [
        ("groq", _call_groq),
        ("gemini", _call_gemini),
        ("openrouter", _call_openrouter),
    ]

    async with httpx.AsyncClient() as client:
        for name, fn in providers:
            raw = await fn(client, settings, user_prompt)
            # #region agent log
            dbg(
                "B",
                "router.py:generate_bubble",
                "provider_attempt",
                {
                    "provider": name,
                    "raw_is_none": raw is None,
                    "raw_len": len(raw) if raw else 0,
                },
            )
            # #endregion
            if raw is None:
                continue
            tracker.record(name, calls=1)
            parsed = _parse_bubble(raw, expected_mood=mood)
            # #region agent log
            dbg(
                "B",
                "router.py:generate_bubble",
                "provider_parse",
                {"provider": name, "parsed_ok": parsed is not None},
            )
            # #endregion
            if parsed:
                return parsed

    # #region agent log
    dbg("B", "router.py:generate_bubble", "all_providers_failed", {})
    # #endregion
    return None
