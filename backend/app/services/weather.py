from __future__ import annotations

from typing import Any

import httpx

from app.config import weather_coords

WMO_DESCRIPTIONS_HU: dict[int, str] = {
    0: "tiszta ég",
    1: "főleg derült",
    2: "részben felhős",
    3: "borús",
    45: "ködös",
    48: "jeges köd",
    51: "szitálás",
    53: "szitálás",
    55: "erős szitálás",
    61: "eső",
    63: "eső",
    65: "erős eső",
    71: "hó",
    73: "hó",
    75: "erős hó",
    80: "zápor",
    81: "zápor",
    82: "hevület",
    95: "vihar",
}


def weather_to_mood(code: int) -> str:
    # Clear / mostly clear -> upbeat
    if code in (0, 1):
        return "happy"
    # Snow -> cozy, quiet
    if code in (71, 73, 75):
        return "cozy"
    # Grey, foggy, rainy or stormy -> melancholy ("bad weather" per design)
    if code in (3, 45, 48, 51, 53, 55, 61, 63, 65, 80, 81, 82, 95):
        return "melancholy"
    return "idle"


async def fetch_weather(profile: dict[str, Any]) -> dict[str, Any] | None:
    if not profile.get("modules_enabled", {}).get("weather", True):
        return None

    lat, lon, city = weather_coords(profile)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code",
        "timezone": profile.get("locations", {}).get("timezone", "Europe/Budapest"),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        return None

    current = data.get("current", {})
    code = int(current.get("weather_code", 0))
    temp = current.get("temperature_2m")
    desc = WMO_DESCRIPTIONS_HU.get(code, "változó idő")

    return {
        "city": city,
        "temp_c": round(temp, 1) if temp is not None else None,
        "description_hu": desc,
        "weather_code": code,
        "mood_hint": weather_to_mood(code),
    }
