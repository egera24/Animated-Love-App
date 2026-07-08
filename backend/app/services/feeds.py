from __future__ import annotations

import logging
from typing import Any

import feedparser
import httpx
from sqlalchemy.orm import Session

from app.services.content_cache import get_cached, set_cached
from app.services.llm.router import generate_chat_reply
from app.services.mood import _today_in_tz

logger = logging.getLogger(__name__)

FEED_MODULES = ("news", "health")
_MAX_ITEMS = 6

_SUMMARY_SYSTEM = {
    "news": (
        "Te Fahéj vagy, egy kedves társ. Foglald össze az alábbi hírcímeket 2–4 meleg, "
        "közérthető magyar mondatban Edinának. CSAK a megadott címekből dolgozz, ne találj "
        "ki semmit. A hangnem legyen könnyed és barátságos."
    ),
    "health": (
        "Te Fahéj vagy, egy kedves társ. Edina 1-es típusú cukorbeteg, és érdeklik a GLP-1 "
        "és T1D témák. Foglald össze az alábbi egészségügyi híreket 2–4 közérthető magyar "
        "mondatban. CSAK a megadott címekből dolgozz, ne találj ki semmit. FONTOS: ez "
        "tájékoztatás, NEM orvosi tanács — zárd azzal, hogy részletekért kérdezze a kezelőorvosát."
    ),
}


def _feed_urls(profile: dict[str, Any], module: str) -> list[str]:
    feeds = profile.get("feeds", {}) or {}
    urls = feeds.get(module, [])
    return [u for u in urls if isinstance(u, str) and u.strip()]


async def _fetch_entries(urls: list[str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = await client.get(url, headers={"User-Agent": "FahejApp/1.0"})
                resp.raise_for_status()
                parsed = feedparser.parse(resp.content)
            except Exception as e:
                logger.warning("Feed fetch failed for %s: %s", url, e)
                continue
            for item in parsed.entries[:_MAX_ITEMS]:
                title = (item.get("title") or "").strip()
                if not title:
                    continue
                entries.append({"title": title, "link": (item.get("link") or "").strip()})
    return entries[:_MAX_ITEMS]


def _fallback_text(module: str, entries: list[dict[str, str]]) -> str:
    heading = "Mai hírek" if module == "news" else "Egészség hírek"
    bullets = "\n".join(f"• {e['title']}" for e in entries)
    return f"{heading}:\n{bullets}"


async def _summarize(module: str, entries: list[dict[str, str]], db: Session) -> str:
    titles = "\n".join(f"- {e['title']}" for e in entries)
    system_prompt = _SUMMARY_SYSTEM.get(module, _SUMMARY_SYSTEM["news"])
    try:
        summary = await generate_chat_reply(
            db,
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": titles}],
            temperature=0.6,
        )
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Feed summary failed for %s: %s", module, e)
        summary = None
    return summary.strip() if summary else _fallback_text(module, entries)


async def generate_feed_digest(
    db: Session,
    module: str,
    profile: dict[str, Any],
) -> dict[str, Any] | None:
    content_date = _today_in_tz(profile).isoformat()
    cached = get_cached(db, content_date, module)
    if cached:
        return cached

    urls = _feed_urls(profile, module)
    if not urls:
        return None

    entries = await _fetch_entries(urls)
    if not entries:
        return None

    text = await _summarize(module, entries, db)
    title = "Mai hírek" if module == "news" else "Egészség — friss hírek"
    payload: dict[str, Any] = {
        "module": module,
        "text": text,
        "title": title,
        "items": [{"title": e["title"], "url": e["link"]} for e in entries],
        "source": "rss",
        "content_date": content_date,
    }
    set_cached(db, content_date, module, payload)
    return payload
