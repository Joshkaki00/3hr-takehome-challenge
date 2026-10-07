"""Mood storage in Redis. Tests mock the redis client."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone


class MoodError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _mood_key(day, anon_id=None):
    if anon_id:
        return f"moods:{anon_id}:{day}"
    return f"moods:{day}"


def _normalize_day(day=None):
    if day is None:
        return date.today().isoformat()
    if isinstance(day, date):
        return day.isoformat()
    day = str(day).strip()
    if not day:
        raise MoodError("date is required", status_code=400)
    # validate YYYY-MM-DD
    date.fromisoformat(day)
    return day


def save_mood(redis_client, *, mood, city, weather, day=None, anon_id=None, overwrite=True):
    """
    Save one mood entry for a day.
    Default: overwrite if the same day already has an entry.
    anon_id: optional anonymous user ID; if provided, mood is scoped to that user.
    """
    mood = (mood or "").strip()
    city = (city or "").strip()
    if not mood:
        raise MoodError("mood is required", status_code=400)
    if not city:
        raise MoodError("city is required", status_code=400)
    if weather is None:
        raise MoodError("weather snapshot is required", status_code=400)

    day_s = _normalize_day(day)
    key = _mood_key(day_s, anon_id)
    existing = redis_client.get(key)
    if existing is not None and not overwrite:
        raise MoodError(f"mood already logged for {day_s}", status_code=409)

    entry = {
        "date": day_s,
        "mood": mood,
        "city": city,
        "weather": weather,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    redis_client.set(key, json.dumps(entry))
    return entry


def get_mood(redis_client, day=None, anon_id=None):
    day_s = _normalize_day(day)
    raw = redis_client.get(_mood_key(day_s, anon_id))
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def list_moods(redis_client, anon_id=None):
    # KEYS blocks Redis on large keyspaces; SCAN pages incrementally.
    # https://redis.io/docs/latest/commands/scan/
    if anon_id:
        pattern = f"moods:{anon_id}:*"
    else:
        pattern = "moods:*"
    keys = sorted(redis_client.scan_iter(match=pattern, count=100))
    out = []
    for key in keys:
        raw = redis_client.get(key)
        if raw is None:
            continue
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        out.append(json.loads(raw))
    return out
