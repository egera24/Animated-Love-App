from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import ChatMessage
from app.services.expression import expression_from_chat
from app.services.fallbacks import pick_message
from app.services.llm.router import generate_chat_reply
from app.services.mood import MoodResult, resolve_mood
from app.services.weather import fetch_weather


@dataclass
class ChatResult:
    reply: str
    mood: str
    expression: str
    source: str


def _persona_intro(profile: dict[str, Any], character_id: str) -> str:
    recipient = profile.get("recipient", {}).get("name", "Edina")
    if character_id == "self":
        av = profile.get("self_avatar", {})
        name = av.get("name", "Én")
        personality = av.get("personality", "meleg, gondoskodó")
        return (
            f"Te {name} vagy — {recipient} szerető társa. Melegen, gondoskodóan és "
            f"kicsit humorosan beszélgetsz vele, első személyben, magyarul. "
            f"Személyiség: {personality}."
        )
    hog = profile.get("hedgehog", {})
    name = hog.get("name", "Fahéj")
    personality = hog.get("personality", "playful, humorous")
    return (
        f"Te {name} vagy, egy játékos, humoros sün, aki {recipient} társaságában él "
        f"egy ajándék appban. Első személyben, kedvesen és könnyed humorral beszélsz, "
        f"magyarul. Személyiség: {personality}."
    )


def build_system_prompt(
    profile: dict[str, Any],
    character_id: str,
    mood_result: MoodResult,
    weather: dict[str, Any] | None,
    *,
    memory_context: str = "",
) -> str:
    recipient = profile.get("recipient", {}).get("name", "Edina")
    lines = [_persona_intro(profile, character_id)]

    lines.append(
        "Beszélgess vele természetesen, mint egy figyelmes társ: tegyél fel kérdéseket, "
        "reagálj arra amit mond, és tartsd a választ rövidnek (1–4 mondat). Soha ne "
        "legyél gúnyos vagy bántó. NE adj orvosi tanácsot — ha egészségről van szó, "
        "légy támogató és javasold, hogy kérdezze meg a kezelőorvosát."
    )

    lines.append(f"Mai hangulat: {mood_result.mood}.")
    if mood_result.is_birthday:
        lines.append(f"Ma {recipient} születésnapja — legyél ünnepi és figyelmes.")
    elif mood_result.special_date_label:
        lines.append(f"Különleges nap ma: {mood_result.special_date_label}.")
    if mood_result.behavior:
        lines.append(f"Viselkedési útmutató mára: {mood_result.behavior}")
    if mood_result.topic_hints:
        lines.append(
            "Ha jól esik neki, finoman terelhetsz ezekre a témákra: "
            + json.dumps(mood_result.topic_hints, ensure_ascii=False)
        )

    if weather and weather.get("temp_c") is not None:
        lines.append(
            f"Időjárás {weather.get('city', 'Szeged')}: {weather.get('temp_c')}°C, "
            f"{weather.get('description_hu', '')}."
        )

    interests = profile.get("interests")
    if interests:
        lines.append(
            "Érdeklődései (utalhatsz rájuk): " + json.dumps(interests, ensure_ascii=False)
        )

    health = profile.get("health")
    if health:
        lines.append(
            "Egészségügyi háttér (érzékenyen kezeld, nem orvosi tanács): "
            + json.dumps(health, ensure_ascii=False)
        )

    if memory_context:
        lines.append("Amit róla tudsz (emlékek):\n" + memory_context)

    return "\n".join(lines)


def load_recent_messages(db: Session, character_id: str, *, limit: int) -> list[ChatMessage]:
    rows = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.character_id == character_id)
        .order_by(ChatMessage.id.desc())
        .limit(limit)
    ).all()
    return list(reversed(rows))


def _save_message(
    db: Session,
    *,
    role: str,
    character_id: str,
    content: str,
    mood: str | None,
    expression: str | None,
) -> None:
    db.add(
        ChatMessage(
            role=role,
            character_id=character_id,
            content=content,
            mood=mood,
            expression=expression,
        )
    )
    db.commit()


def _fallback_reply(mood_result: MoodResult, profile: dict[str, Any]) -> str:
    base = pick_message(mood_result.mood)
    return base


async def generate_reply(
    db: Session,
    *,
    profile: dict[str, Any],
    character_id: str,
    user_text: str,
    memory_context: str = "",
) -> ChatResult:
    settings = get_settings()
    weather = await fetch_weather(profile)
    weather_mood = weather.get("mood_hint") if weather else None
    mood_result = resolve_mood(profile, weather_mood=weather_mood)

    system_prompt = build_system_prompt(
        profile,
        character_id,
        mood_result,
        weather,
        memory_context=memory_context,
    )

    history = load_recent_messages(db, character_id, limit=settings.chat_history_turns * 2)
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": user_text})

    reply = await generate_chat_reply(db, system_prompt=system_prompt, messages=messages)
    source = "llm"
    if not reply:
        reply = _fallback_reply(mood_result, profile)
        source = "static"

    expression = expression_from_chat(mood_result.mood, user_text=user_text)

    _save_message(
        db,
        role="user",
        character_id=character_id,
        content=user_text,
        mood=mood_result.mood,
        expression=None,
    )
    _save_message(
        db,
        role="assistant",
        character_id=character_id,
        content=reply,
        mood=mood_result.mood,
        expression=expression,
    )

    return ChatResult(reply=reply, mood=mood_result.mood, expression=expression, source=source)
