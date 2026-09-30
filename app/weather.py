"""OpenWeather helpers. Unit tests mock HTTP; no live key needed.

Uses Geocoding + Current Weather Data 2.5 (free tier).
One Call 4.0 needs a separate paid plan, so we do not use it.
"""

from __future__ import annotations

import requests

OWM_GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
OWM_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherError(Exception):
    """Weather lookup failed in a way the API should report."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def require_api_key(api_key):
    if not api_key:
        raise WeatherError("OPENWEATHER_API_KEY is missing", status_code=500)


def geocode_city(city, api_key, session=None):
    """Resolve city name to lat/lon via OpenWeather geocoding."""
    require_api_key(api_key)
    city = (city or "").strip()
    if not city:
        raise WeatherError("city is required", status_code=400)

    http = session or requests
    resp = http.get(
        OWM_GEO_URL,
        params={"q": city, "limit": 1, "appid": api_key},
        timeout=10,
    )
    if resp.status_code == 401:
        raise WeatherError("invalid OpenWeather API key", status_code=502)
    if resp.status_code >= 500:
        raise WeatherError("weather service unavailable", status_code=502)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise WeatherError(f"city not found: {city}", status_code=404)
    place = data[0]
    return {
        "name": place.get("name", city),
        "lat": place["lat"],
        "lon": place["lon"],
        "country": place.get("country"),
    }


def fetch_current_weather(lat, lon, api_key, session=None, units="metric"):
    """Fetch Current Weather Data 2.5 for lat/lon (free tier)."""
    require_api_key(api_key)
    http = session or requests
    resp = http.get(
        OWM_CURRENT_URL,
        params={
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": units,
        },
        timeout=10,
    )
    if resp.status_code == 401:
        raise WeatherError("invalid OpenWeather API key", status_code=502)
    if resp.status_code == 404:
        raise WeatherError("weather not found for location", status_code=404)
    if resp.status_code >= 500:
        raise WeatherError("weather service unavailable", status_code=502)
    resp.raise_for_status()
    payload = resp.json()
    main = payload.get("main") or {}
    weather0 = (payload.get("weather") or [{}])[0]
    return {
        "temp": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity": main.get("humidity"),
        "description": weather0.get("description"),
        "main": weather0.get("main"),
    }


def weather_for_city(city, api_key, session=None, units="metric"):
    place = geocode_city(city, api_key, session=session)
    current = fetch_current_weather(
        place["lat"], place["lon"], api_key, session=session, units=units
    )
    return {
        "city": place["name"],
        "country": place.get("country"),
        "lat": place["lat"],
        "lon": place["lon"],
        "weather": current,
    }
