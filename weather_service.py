"""
weather_service.py — user-directed real weather for mini-social-media.

Design:
- Default provider: Open-Meteo (free, no API key, no usage limits, HTTPS, CORS-friendly).
- Configurable via MINI_SOCIAL_WEATHER_PROVIDER env var.
- Optional API key env var for providers that require one.
- Geo-coding is done via Open-Meteo's open geocoding API.
- Falls back to deterministic pseudo-weather on network or parsing failure.
- Deterministic fallback preserved for tests/offline environments.

Supported free providers
------------------------
| Provider            | API key required? | Notes |
|---------------------|-------------------|-------|
| open-meteo          | No                | Default. Open data. HTTPS. Global. |
| openweathermap      | Yes               | Free tier: 60 calls/min, requires key. |
| weatherapi          | Yes               | Free tier: 1M calls/month, requires key. |
| national-weather-service | No           | US-only (weather.gov). Free, public. |
| pseudo              | n/a               | Original deterministic local weather. |

Environment variables
---------------------
MINI_SOCIAL_WEATHER_PROVIDER   open-meteo | openweathermap | weatherapi | national-weather-service | pseudo
MINI_SOCIAL_WEATHER_API_KEY  required for openweathermap / weatherapi
MINI_SOCIAL_WEATHER_TIMEOUT  HTTP timeout in seconds (default 6)
"""

import os
import json
import hashlib
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple


DEFAULT_PROVIDER = os.environ.get("MINI_SOCIAL_WEATHER_PROVIDER", "open-meteo")
API_KEY = os.environ.get("MINI_SOCIAL_WEATHER_API_KEY", "")
TIMEOUT = int(os.environ.get("MINI_SOCIAL_WEATHER_TIMEOUT", "6"))

# Open-Meteo WMO weather interpretation codes -> human-readable label
OPEN_METEO_CODES = {
    0: "Clear",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Light Freezing Drizzle",
    57: "Dense Freezing Drizzle",
    61: "Light Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Light Freezing Rain",
    67: "Heavy Freezing Rain",
    71: "Light Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Hail",
    99: "Heavy Thunderstorm with Hail",
}


def _fetch_json(url: str) -> Optional[Dict[str, Any]]:
    """Fetch and parse JSON from a URL with a tight timeout."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "mini-social-media/1.0.0"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            json.JSONDecodeError, OSError, ValueError):
        return None


def _pseudo_weather(location_general: str, date_str: Optional[str] = None) -> Dict[str, Any]:
    """Original deterministic fallback weather."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_of_year = datetime.strptime(date_str, "%Y-%m-%d").timetuple().tm_yday
    h = hashlib.md5(f"{location_general.lower().strip()}:{date_str}".encode()).hexdigest()
    conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Rainy", "Snowy", "Clear"]
    condition = conditions[int(h[:2], 16) % len(conditions)]
    base_temp = 55 + (int(h[2:4], 16) % 30)
    seasonal_offset = int(10 * (1 if day_of_year < 60 or day_of_year > 300 else -1) * (abs(day_of_year - 180) / 180))
    low = base_temp + seasonal_offset - 5
    high = base_temp + seasonal_offset + 8
    return {
        "condition": condition,
        "low": low,
        "high": high,
        "location": location_general,
        "date": date_str,
        "source": "pseudo",
    }


def _geocode_open_meteo(location_general: str) -> Optional[Tuple[float, float]]:
    """Return (lat, lon) for a free-form location string via Open-Meteo."""
    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={urllib.parse.quote(location_general)}&count=1&language=en&format=json"
    )
    data = _fetch_json(url)
    if not data or "results" not in data or not data["results"]:
        return None
    result = data["results"][0]
    return (float(result.get("latitude", 0)), float(result.get("longitude", 0)))


def _open_meteo_weather(location_general: str, date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch current daily forecast from Open-Meteo."""
    coords = _geocode_open_meteo(location_general)
    if coords is None:
        return None
    lat, lon = coords
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=weathercode,temperature_2m_max,temperature_2m_min"
        "&temperature_unit=fahrenheit&windspeed_unit=mph&precipitation_unit=inch"
        "&timezone=auto"
    )
    if date_str:
        url += f"&start_date={date_str}&end_date={date_str}"
    data = _fetch_json(url)
    if not data or "daily" not in data or not data["daily"].get("time"):
        return None
    daily = data["daily"]
    idx = 0
    if date_str and date_str in daily["time"]:
        idx = daily["time"].index(date_str)
    code = int(daily.get("weathercode", [0])[idx])
    high = round(float(daily.get("temperature_2m_max", [0])[idx]))
    low = round(float(daily.get("temperature_2m_min", [0])[idx]))
    return {
        "condition": OPEN_METEO_CODES.get(code, "Unknown"),
        "low": low,
        "high": high,
        "location": location_general,
        "date": date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "open-meteo",
    }


def _openweathermap_weather(location_general: str, _date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch current weather from OpenWeatherMap (free tier with key)."""
    if not API_KEY:
        return None
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={urllib.parse.quote(location_general)}&appid={API_KEY}&units=imperial"
    )
    data = _fetch_json(url)
    if not data or "main" not in data:
        return None
    main = data["main"]
    condition = data["weather"][0]["main"] if data.get("weather") else "Unknown"
    return {
        "condition": condition,
        "low": round(float(main.get("temp_min", 0))),
        "high": round(float(main.get("temp_max", 0))),
        "location": location_general,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "openweathermap",
    }


def _weatherapi_weather(location_general: str, _date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch current weather from WeatherAPI (free tier with key)."""
    if not API_KEY:
        return None
    url = (
        "https://api.weatherapi.com/v1/forecast.json"
        f"?key={API_KEY}&q={urllib.parse.quote(location_general)}&days=1&aqi=no&alerts=no"
    )
    data = _fetch_json(url)
    if not data or "forecast" not in data:
        return None
    day = data["forecast"]["forecastday"][0]["day"]
    return {
        "condition": day.get("condition", {}).get("text", "Unknown"),
        "low": round(float(day.get("mintemp_f", 0))),
        "high": round(float(day.get("maxtemp_f", 0))),
        "location": location_general,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "weatherapi",
    }


def _nws_weather(location_general: str, _date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch current forecast from U.S. National Weather Service (weather.gov). US-only."""
    # First geocode via the Census geocoder (free, public)
    geocode_url = (
        "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        f"?address={urllib.parse.quote(location_general)}&benchmark=4&format=json"
    )
    geo = _fetch_json(geocode_url)
    if not geo or "result" not in geo or not geo["result"].get("addressMatches"):
        return None
    match = geo["result"]["addressMatches"][0]
    coords = match["coordinates"]
    lat, lon = float(coords["y"]), float(coords["x"])

    # Get NWS gridpoint
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    points = _fetch_json(points_url)
    if not points or "properties" not in points:
        return None
    forecast_url = points["properties"].get("forecast")
    if not forecast_url:
        return None
    forecast = _fetch_json(forecast_url)
    if not forecast or "properties" not in forecast or not forecast["properties"].get("periods"):
        return None
    period = forecast["properties"]["periods"][0]
    return {
        "condition": period.get("shortForecast", "Unknown"),
        "low": round(float(period.get("temperature", 0))) if period.get("isDaytime") else None,
        "high": round(float(period.get("temperature", 0))) if not period.get("isDaytime") else None,
        "location": location_general,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "national-weather-service",
    }


_PROVIDER_FUNCS = {
    "open-meteo": _open_meteo_weather,
    "openweathermap": _openweathermap_weather,
    "weatherapi": _weatherapi_weather,
    "national-weather-service": _nws_weather,
    "pseudo": _pseudo_weather,
}


def get_weather(location_general: str, date_str: Optional[str] = None, provider: Optional[str] = None) -> Dict[str, Any]:
    """Return weather for a location.

    Uses configured provider and falls back to pseudo-weather on any failure.
    The returned dict always contains: condition, low, high, location, date, source.
    """
    provider = (provider or DEFAULT_PROVIDER).lower().strip()
    func = _PROVIDER_FUNCS.get(provider, _open_meteo_weather)
    try:
        result = func(location_general, date_str)
    except Exception:
        result = None
    if result is None:
        result = _pseudo_weather(location_general, date_str)
        result["fallback_reason"] = f"{provider} unavailable"
    return result


def supported_providers() -> Dict[str, Dict[str, Any]]:
    """Return metadata about supported weather providers for UI/help pages."""
    return {
        "open-meteo": {
            "name": "Open-Meteo",
            "key_required": False,
            "url": "https://open-meteo.com",
            "notes": "Default. Free, global, no API key.",
        },
        "openweathermap": {
            "name": "OpenWeatherMap",
            "key_required": True,
            "url": "https://openweathermap.org/api",
            "notes": "Free tier: 60 calls/min. API key required.",
        },
        "weatherapi": {
            "name": "WeatherAPI",
            "key_required": True,
            "url": "https://www.weatherapi.com",
            "notes": "Free tier: 1M calls/month. API key required.",
        },
        "national-weather-service": {
            "name": "National Weather Service (weather.gov)",
            "key_required": False,
            "url": "https://www.weather.gov/documentation/services-web-api",
            "notes": "US-only. Free, public, no API key.",
        },
        "pseudo": {
            "name": "Pseudo-Weather",
            "key_required": False,
            "url": "",
            "notes": "Original deterministic local-only fallback.",
        },
    }
