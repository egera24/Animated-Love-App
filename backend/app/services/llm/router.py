from __future__ import annotations

import json
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import LlmProviderEntry, Settings, get_settings, load_llm_catalog
from app.services.llm.schemas import BubbleLLMResponse
from app.services.llm.usage import UsageTracker

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Te Fahéj vagy, egy játékos, humoros sün. Edinának írsz rövid, meleg magyar szöveget egy ajándék webapp buborékába.
Első személyben beszélj. Legyél kedves, könnyed humorral — soha ne legyél gúnyos vagy bántó.
Válaszod KIZÁRÓLAG érvényes JSON legyen, más szöveg nélkül:
{"bubble_text": "...", "mood": "...", "language": "hu"}
A mood mező egyezzen a kért hangulattal (ne változtasd meg a naptári logikát)."""

BubbleCallFn = Callable[
    [httpx.AsyncClient, Settings, str, str, float],
    Awaitable[str | None],
]
ChatCallFn = Callable[
    [httpx.AsyncClient, Settings, str, str, str, list[dict[str, str]], float],
    Awaitable[str | None],
]


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
    if behavior := context.get("behavior"):
        lines.append(f"Viselkedési útmutató: {behavior}")
    if topic_hints := context.get("topic_hints"):
        lines.append(
            f"Ajánlható témák (finoman): {json.dumps(topic_hints, ensure_ascii=False)}"
        )
    if weather := context.get("weather"):
        lines.append(
            f"Időjárás ({weather.get('city', 'Szeged')}): "
            f"{weather.get('temp_c')}°C, {weather.get('description_hu', '')}"
        )
    interests = context.get("interests")
    if interests:
        lines.append(f"Érdeklődések (utalhat rájuk finoman): {json.dumps(interests, ensure_ascii=False)}")
    if context.get("interactive_refresh"):
        vid = context.get("variation_id") or "?"
        lines.append(
            f"Edina most rád kattintott (frissítés #{vid}) — kötelezően ÚJ szöveg, más szavakkal és megfoglalással."
        )
        if prev := context.get("previous_bubble"):
            lines.append(f"Az előző buborék szövege (NE ismételd, ne parafrázis ugyanazzal a kezdéssel): «{prev}»")
    lines.append("Írj 1–3 rövid mondatot a bubble_text mezőbe; időjárást említheted ha releváns.")
    return "\n".join(lines)


async def _call_groq(
    client: httpx.AsyncClient,
    settings: Settings,
    model: str,
    user_prompt: str,
    *,
    temperature: float = 0.8,
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
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": 400,
            },
            timeout=30.0,
        )
        if r.status_code in (401, 403, 429) or r.status_code >= 500:
            logger.warning("Groq HTTP %s model=%s", r.status_code, model)
            return None
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("Groq error model=%s: %s", model, e)
        return None


async def _call_gemini(
    client: httpx.AsyncClient,
    settings: Settings,
    model: str,
    user_prompt: str,
    *,
    temperature: float = 0.8,
) -> str | None:
    if not settings.gemini_api_key:
        return None
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
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
                "generationConfig": {"temperature": temperature, "maxOutputTokens": 400},
            },
            timeout=30.0,
        )
        if r.status_code in (401, 403, 429) or r.status_code >= 500:
            logger.warning("Gemini HTTP %s model=%s", r.status_code, model)
            return None
        r.raise_for_status()
        data = r.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        if not parts:
            return None
        return parts[0].get("text", "")
    except Exception as e:
        logger.warning("Gemini error model=%s: %s", model, e)
        return None


async def _call_openrouter(
    client: httpx.AsyncClient,
    settings: Settings,
    model: str,
    user_prompt: str,
    *,
    temperature: float = 0.8,
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
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": 400,
            },
            timeout=45.0,
        )
        if r.status_code in (401, 403, 429) or r.status_code >= 500:
            logger.warning("OpenRouter HTTP %s model=%s", r.status_code, model)
            return None
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("OpenRouter error model=%s: %s", model, e)
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


async def _chat_groq(
    client: httpx.AsyncClient,
    settings: Settings,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    *,
    temperature: float,
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
                "model": model,
                "messages": [{"role": "system", "content": system_prompt}, *messages],
                "temperature": temperature,
                "max_tokens": 600,
            },
            timeout=30.0,
        )
        if r.status_code in (401, 403, 429) or r.status_code >= 500:
            logger.warning("Groq chat HTTP %s model=%s", r.status_code, model)
            return None
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("Groq chat error model=%s: %s", model, e)
        return None


async def _chat_gemini(
    client: httpx.AsyncClient,
    settings: Settings,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    *,
    temperature: float,
) -> str | None:
    if not settings.gemini_api_key:
        return None
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    contents = [
        {
            "role": "user" if m["role"] == "user" else "model",
            "parts": [{"text": m["content"]}],
        }
        for m in messages
    ]
    try:
        r = await client.post(
            url,
            params={"key": settings.gemini_api_key},
            json={
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": contents,
                "generationConfig": {"temperature": temperature, "maxOutputTokens": 600},
            },
            timeout=30.0,
        )
        if r.status_code in (401, 403, 429) or r.status_code >= 500:
            logger.warning("Gemini chat HTTP %s model=%s", r.status_code, model)
            return None
        r.raise_for_status()
        data = r.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        if not parts:
            return None
        return parts[0].get("text", "")
    except Exception as e:
        logger.warning("Gemini chat error model=%s: %s", model, e)
        return None


async def _chat_openrouter(
    client: httpx.AsyncClient,
    settings: Settings,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    *,
    temperature: float,
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
                "model": model,
                "messages": [{"role": "system", "content": system_prompt}, *messages],
                "temperature": temperature,
                "max_tokens": 600,
            },
            timeout=45.0,
        )
        if r.status_code in (401, 403, 429) or r.status_code >= 500:
            logger.warning("OpenRouter chat HTTP %s model=%s", r.status_code, model)
            return None
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("OpenRouter chat error model=%s: %s", model, e)
        return None


_BUBBLE_FNS: dict[str, BubbleCallFn] = {
    "groq": _call_groq,
    "gemini": _call_gemini,
    "openrouter": _call_openrouter,
}

_CHAT_FNS: dict[str, ChatCallFn] = {
    "groq": _chat_groq,
    "gemini": _chat_gemini,
    "openrouter": _chat_openrouter,
}


async def _try_bubble_catalog(
    catalog: list[LlmProviderEntry],
    client: httpx.AsyncClient,
    settings: Settings,
    user_prompt: str,
    *,
    temperature: float,
) -> tuple[str, str, str] | None:
    for provider in catalog:
        fn = _BUBBLE_FNS.get(provider.name)
        if fn is None:
            continue
        for model in provider.models:
            raw = await fn(client, settings, model, user_prompt, temperature=temperature)
            if raw is None:
                logger.info("LLM fallback: %s/%s failed → trying next", provider.name, model)
                continue
            logger.info("LLM ok: %s/%s", provider.name, model)
            return provider.name, model, raw
    return None


async def _try_chat_catalog(
    catalog: list[LlmProviderEntry],
    client: httpx.AsyncClient,
    settings: Settings,
    system_prompt: str,
    messages: list[dict[str, str]],
    *,
    temperature: float,
) -> tuple[str, str, str] | None:
    for provider in catalog:
        fn = _CHAT_FNS.get(provider.name)
        if fn is None:
            continue
        for model in provider.models:
            raw = await fn(
                client, settings, model, system_prompt, messages, temperature=temperature
            )
            if raw is None:
                logger.info("LLM fallback: %s/%s failed → trying next", provider.name, model)
                continue
            logger.info("LLM ok: %s/%s", provider.name, model)
            return provider.name, model, raw
    return None


async def generate_chat_reply(
    db: Session,
    *,
    system_prompt: str,
    messages: list[dict[str, str]],
    temperature: float = 0.9,
) -> str | None:
    """Multi-turn conversational reply. Shares the provider/model fallback chain with
    bubbles but has its own daily budget (category="chat")."""
    settings = get_settings()
    if not settings.has_any_llm_key():
        return None

    tracker = UsageTracker(
        db,
        daily_call_limit=settings.llm_chat_daily_call_limit,
        category="chat",
    )
    if not tracker.can_call():
        logger.info("LLM chat daily call limit reached")
        return None

    catalog = load_llm_catalog(settings)
    if not catalog:
        return None

    async with httpx.AsyncClient() as client:
        result = await _try_chat_catalog(
            catalog, client, settings, system_prompt, messages, temperature=temperature
        )
        if result is None:
            return None
        provider, model, raw = result
        tracker.record(f"{provider}/{model}", calls=1)
        text = raw.strip()
        if text:
            return text

    return None


async def generate_bubble(
    db: Session,
    *,
    mood: str,
    profile: dict[str, Any],
    context: dict[str, Any],
) -> BubbleLLMResponse | None:
    settings = get_settings()
    if not settings.has_any_llm_key():
        return None

    tracker = UsageTracker(db, daily_call_limit=settings.llm_daily_call_limit)
    if not tracker.can_call():
        logger.info("LLM daily call limit reached")
        return None

    catalog = load_llm_catalog(settings)
    if not catalog:
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

    temperature = 1.0 if context.get("interactive_refresh") else 0.8

    async with httpx.AsyncClient() as client:
        result = await _try_bubble_catalog(
            catalog, client, settings, user_prompt, temperature=temperature
        )
        if result is None:
            return None
        provider, model, raw = result
        tracker.record(f"{provider}/{model}", calls=1)
        parsed = _parse_bubble(raw, expected_mood=mood)
        if parsed:
            return parsed

    return None
