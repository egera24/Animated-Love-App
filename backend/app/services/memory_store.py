from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import DATA_DIR, get_settings
from app.db.models import Memory
from app.services.llm.router import generate_chat_reply

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = DATA_DIR / "knowledge"
KNOWLEDGE_FILE = KNOWLEDGE_DIR / "edina.yaml"
KNOWLEDGE_EXAMPLE = KNOWLEDGE_DIR / "edina.example.yaml"

_STOPWORDS = {
    "a", "az", "és", "hogy", "nem", "is", "de", "vagy", "egy", "ez", "de",
    "the", "and", "you", "for", "with", "that", "this",
}

_MAX_MEMORIES_IN_CONTEXT = 6


def load_knowledge() -> dict[str, Any]:
    """Hand-edited facts about Edina. Falls back to the example template, and is
    safe (returns {}) if neither file is present."""
    path = KNOWLEDGE_FILE if KNOWLEDGE_FILE.exists() else KNOWLEDGE_EXAMPLE
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Failed to read knowledge file: %s", e)
        return {}


def _knowledge_to_lines(knowledge: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key, value in knowledge.items():
        if isinstance(value, (list, tuple)):
            for item in value:
                lines.append(f"- {key}: {item}")
        elif isinstance(value, dict):
            lines.append(f"- {key}: {json.dumps(value, ensure_ascii=False)}")
        else:
            lines.append(f"- {key}: {value}")
    return lines


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"\w+", text.lower())
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


def _score_memory(mem: Memory, query_tokens: set[str]) -> float:
    tokens = _tokenize(mem.text)
    overlap = len(tokens & query_tokens)
    recency = mem.created_at.timestamp() if mem.created_at else 0
    # weight: overlap dominates, then salience, then a small recency nudge
    return overlap * 10 + mem.salience * 2 + recency / 1e12


def get_relevant_memories(db: Session, *, query: str, limit: int = _MAX_MEMORIES_IN_CONTEXT) -> list[Memory]:
    rows = db.scalars(select(Memory)).all()
    if not rows:
        return []
    query_tokens = _tokenize(query)
    ranked = sorted(rows, key=lambda m: _score_memory(m, query_tokens), reverse=True)
    top = ranked[:limit]
    now = datetime.utcnow()
    for m in top:
        m.last_used_at = now
    db.commit()
    return top


def get_memory_context(db: Session, profile: dict[str, Any], *, query: str = "") -> str:
    parts: list[str] = []
    knowledge_lines = _knowledge_to_lines(load_knowledge())
    if knowledge_lines:
        parts.extend(knowledge_lines)
    for mem in get_relevant_memories(db, query=query):
        parts.append(f"- {mem.text}")
    return "\n".join(parts)


_EXTRACT_SYSTEM = (
    "Kinyered a tartós, hasznos tényeket a felhasználó (Edina) üzenetéből, amelyeket "
    "érdemes megjegyezni egy társalgó asszisztensnek (pl. kedvencek, tervek, fontos "
    "emberek, események, preferenciák). Csak valódi, tartós tényeket adj vissza — NE "
    "múló hangulatot vagy kérdést. Válaszod KIZÁRÓLAG egy JSON tömb legyen rövid magyar "
    'mondatokkal, pl. ["Edina szereti a levendulát."]. Ha nincs ilyen tény: []'
)


def _parse_json_array(text: str) -> list[str]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    return [str(x).strip() for x in data if isinstance(x, str) and x.strip()]


def _memory_exists(db: Session, text: str) -> bool:
    existing = db.scalar(select(Memory).where(Memory.text == text))
    return existing is not None


async def extract_and_store(db: Session, profile: dict[str, Any], *, user_text: str) -> list[str]:
    """Best-effort: ask the LLM for durable facts and store new ones.

    Failures are swallowed so a chat turn never breaks because of memory work.
    """
    settings = get_settings()
    if not settings.has_any_llm_key():
        return []
    try:
        raw = await generate_chat_reply(
            db,
            system_prompt=_EXTRACT_SYSTEM,
            messages=[{"role": "user", "content": user_text}],
            temperature=0.2,
        )
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Memory extraction failed: %s", e)
        return []
    if not raw:
        return []

    facts = _parse_json_array(raw)
    stored: list[str] = []
    for fact in facts[:3]:
        if _memory_exists(db, fact):
            continue
        db.add(Memory(kind="fact", text=fact, source="chat", salience=1))
        stored.append(fact)
    if stored:
        db.commit()
    return stored
