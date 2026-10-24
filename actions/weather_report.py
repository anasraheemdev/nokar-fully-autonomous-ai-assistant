"""
actions/weather_report.py — Live Weather Intelligence via OpenWeatherMap REST API.

Features:
  • Queries live temperature, weather conditions, humidity, wind speed, and feels-like temp.
  • Uses API key configured in config/api_keys.json or default key.
  • Defaults to the user's hometown/city (Islamabad) if not specified.
  • Auto-discovered by core.action_loader.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
DEFAULT_WEATHER_KEY = "df73742074c0e0436ab98b31c20c590c"


def _get_weather_key() -> str:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return data.get("weather_api_key", DEFAULT_WEATHER_KEY) or DEFAULT_WEATHER_KEY
        except Exception:
            pass
    return DEFAULT_WEATHER_KEY


def _get_default_city() -> str:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return data.get("default_city", "Islamabad") or "Islamabad"
        except Exception:
            pass
    return "Islamabad"


def get_live_weather(city: str) -> tuple[bool, str, dict]:
    """Fetch live weather from OpenWeatherMap API."""
    key = _get_weather_key()
    city_clean = city.strip()
    encoded_city = urllib.parse.quote(city_clean)
    url = f"https://api.openweathermap.org/data/2.5/weather?q={encoded_city}&appid={key}&units=metric"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Nokar-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))

        city_name = data.get("name", city_clean)
        country = data.get("sys", {}).get("country", "")
        temp = data.get("main", {}).get("temp", 0)
        feels_like = data.get("main", {}).get("feels_like", temp)
        humidity = data.get("main", {}).get("humidity", 0)
        desc = data.get("weather", [{}])[0].get("description", "clear sky").capitalize()
        wind_speed = data.get("wind", {}).get("speed", 0)

        summary = (
            f"Sir, the weather in {city_name}{', ' + country if country else ''} is currently {round(temp)}°C "
            f"with {desc}. Feels like {round(feels_like)}°C, with {humidity}% humidity and wind at {wind_speed} m/s."
        )
        return True, summary, data

    except urllib.error.HTTPError as he:
        if he.code == 404:
            return False, f"Sir, I could not find weather data for '{city_clean}'.", {}
        return False, f"Weather API error ({he.code}): {he.reason}", {}
    except Exception as e:
        return False, f"Could not connect to weather service: {e}", {}


def weather_action(parameters: dict = None, player=None, session_memory=None) -> str:
    params = parameters or {}
    city = params.get("city") or _get_default_city()
    city = str(city).strip() if city else _get_default_city()

    ok, message, data = get_live_weather(city)

    if not ok:
        # Fallback to browser search
        search_query = f"weather in {city}"
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"
        try:
            webbrowser.open(url)
            message = f"Showing the weather for {city} in your browser, sir."
        except Exception:
            pass

    _log(message, player)

    if session_memory:
        try:
            session_memory.set_last_search(query=f"weather {city}", response=message)
        except Exception:
            pass

    return message


def _log(message: str, player=None) -> None:
    print(f"[Weather] {message}")
    if player:
        try:
            player.write_log(f"NOKAR: {message}")
        except Exception:
            pass


# ── Tool declaration (auto-discovered by core/action_loader.py) ──────────────
TOOL = {
    "name": "weather_report",
    "description": (
        "Gives live real-time weather reports for any city (temperature, conditions, "
        "humidity, wind speed, feels-like). Defaults to Anas Raheem's city (Islamabad) if omitted."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "city": {
                "type": "STRING",
                "description": "City name (e.g. Islamabad, Rawalpindi, Multan, London, New York). Default: Islamabad"
            }
        },
        "required": []
    },
    "handler": weather_action,
}
