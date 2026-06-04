from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any
from zoneinfo import ZoneInfo


@dataclass
class MoodResult:
    mood: str
    is_birthday: bool
    is_special_date: bool
    special_date_label: str | None


def _today_in_tz(profile: dict[str, Any]) -> date:
    tz_name = profile.get("locations", {}).get("timezone", "Europe/Budapest")
    from datetime import datetime

    return datetime.now(ZoneInfo(tz_name)).date()


def _mmdd(d: date) -> str:
    return f"{d.month:02d}-{d.day:02d}"


def resolve_mood(profile: dict[str, Any], weather_mood: str | None = None) -> MoodResult:
    today = _today_in_tz(profile)
    today_key = _mmdd(today)
    recipient = profile.get("recipient", {})
    birthday = recipient.get("birthday", "")

    if today_key == birthday:
        return MoodResult(
            mood="celebrate",
            is_birthday=True,
            is_special_date=True,
            special_date_label="Születésnap",
        )

    special_dates = profile.get("special_dates", [])
    # Priority: wedding (11-12) before engagement (08-19) when both could matter — by list order in profile
    for entry in special_dates:
        if entry.get("date") == today_key:
            return MoodResult(
                mood=entry.get("mood", "happy"),
                is_birthday=False,
                is_special_date=True,
                special_date_label=entry.get("label_hu"),
            )

    if weather_mood:
        return MoodResult(
            mood=weather_mood,
            is_birthday=False,
            is_special_date=False,
            special_date_label=None,
        )

    return MoodResult(
        mood="idle",
        is_birthday=False,
        is_special_date=False,
        special_date_label=None,
    )
