from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from app.config import DATA_DIR, ROOT_DIR

FALLBACKS_PATH = DATA_DIR / "fallbacks" / "messages_hu.json"


def _load_messages() -> dict[str, list[str]]:
    if FALLBACKS_PATH.exists():
        with FALLBACKS_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return _default_messages()


def _default_messages() -> dict[str, list[str]]:
    return {
        "idle": [
            "Szia, Edina! Fahéj vagyok — ma is itt szundikálok melletted.",
            "Edina! Csak bekukkantok: ma is jó napod legyen!",
            "Hmm… ma csendes nap. Tökéletes egy kis tea mellé.",
        ],
        "happy": [
            "Edina! Ma olyan jó kedvem van, mintha megtaláltam volna a nap utolsó mogyorót!",
            "Jó nap ez! Mondjuk úgy, fél mogyoróval is boldog vagyok.",
        ],
        "cozy": [
            "Esik odakint? Akkor bevágok a pihébe — te is burkolózz be!",
            "Ilyen időben a legjobb: meleg takaró, tea, és egy kis TLC… sorozat.",
        ],
        "melancholy": [
            "Kicsit borongós ma az ég… de tudod mit? Én itt vagyok, és ez már fél siker.",
            "Szürke idő van, Edina. Bújjunk be egy meleg teához, és meséljünk valami szépet.",
            "Ilyenkor a tüskéim is lekonyulnak egy kicsit — de egy jó film mindent megold.",
        ],
        "comfort": [
            "Itt vagyok veled, Edina. Ha van kedved, meséljünk valami szépet — én figyelek.",
            "Ma egy ölelésnyi közelebb húzódom hozzád. Jó emlékek, egy kis tea?",
            "Bármi is van, ma extra puha vagyok. Mondd, mi tenne mosolygóssá?",
        ],
        "sleepy": [
            "Hó van? Én ilyenkor extra gömbölyűre állítom a tüskéimet.",
            "Csendes, szürke nap — tökéletes egy szundira.",
        ],
        "celebrate": [
            "Edina!!! Ma ünnepelünk! 🎉 (Igen, a tüskéim is konfettinek hiszik magukat.)",
            "Boldog ünnepet! Ha lenne kalapom, most dobálnám — de a tüskéim is elég díszesek.",
        ],
        "curious": [
            "Nézzük a képeket! Vagy… van még mogyoró a háznál?",
        ],
        "birthday": [
            "Edina! Boldog születésnapot! 🎂 Ma én vagyok a hivatalos sünimese-felolvasó!",
            "Boldog születésnapot! Ígérem, ma nem morcoskodom — csak ha elfogy a torta.",
        ],
        "wedding_anniversary": [
            "Esküvői évforduló! Edina, ma különösen sok szeretet pörög a levegőben — én is érzem, pedig csak sün vagyok.",
        ],
        "engagement_anniversary": [
            "Eljegyzési évforduló! Még mindig libabőrös vagyok tőle — tüskékben is lehet?",
        ],
        "weather_intro": [
            "Nézzük az időjárást {city}-en: {temp}°C, {desc}.",
        ],
    }


def _ensure_fallback_file() -> None:
    FALLBACKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FALLBACKS_PATH.exists():
        with FALLBACKS_PATH.open("w", encoding="utf-8") as f:
            json.dump(_default_messages(), f, ensure_ascii=False, indent=2)


def pick_message(key: str, **kwargs: str) -> str:
    _ensure_fallback_file()
    messages = _load_messages()
    pool = messages.get(key) or messages.get("idle", ["Szia, Edina!"])
    text = random.choice(pool)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text


def build_bubble_text(
    profile: dict[str, Any],
    mood: str,
    *,
    is_birthday: bool,
    special_label: str | None,
    weather: dict[str, Any] | None,
) -> str:
    hedgehog = profile.get("hedgehog", {}).get("name", "Fahéj")
    recipient = profile.get("recipient", {}).get("name", "Edina")

    if is_birthday:
        main = pick_message("birthday")
    elif special_label:
        if "esküvő" in special_label.lower():
            main = pick_message("wedding_anniversary")
        elif "eljegyz" in special_label.lower():
            main = pick_message("engagement_anniversary")
        else:
            main = pick_message("celebrate")
    else:
        main = pick_message(mood)

    parts = [main]

    if weather and weather.get("temp_c") is not None:
        intro = pick_message(
            "weather_intro",
            city=weather.get("city", "Szeged"),
            temp=str(weather["temp_c"]),
            desc=weather.get("description_hu", ""),
        )
        parts.append(intro)

    # Sign off occasionally
    if random.random() < 0.3:
        parts.append(f"— {hedgehog} 🦔")

    return " ".join(parts)
