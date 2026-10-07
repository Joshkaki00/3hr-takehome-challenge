import json
from unittest.mock import MagicMock

import pytest

from app.moods import MoodError, get_mood, list_moods, save_mood


def test_save_mood_requires_mood():
    redis_client = MagicMock()
    with pytest.raises(MoodError) as exc:
        save_mood(redis_client, mood="", city="Seattle", weather={"temp": 1})
    assert exc.value.status_code == 400


def test_save_mood_requires_city():
    redis_client = MagicMock()
    with pytest.raises(MoodError) as exc:
        save_mood(redis_client, mood="ok", city="", weather={"temp": 1})
    assert exc.value.status_code == 400


def test_save_mood_writes_json():
    redis_client = MagicMock()
    redis_client.get.return_value = None

    entry = save_mood(
        redis_client,
        mood="chill",
        city="Seattle",
        weather={"temp": 12, "main": "Rain"},
        day="2026-09-30",
    )
    assert entry["mood"] == "chill"
    assert entry["date"] == "2026-09-30"
    redis_client.set.assert_called_once()
    key, raw = redis_client.set.call_args[0]
    assert key == "moods:2026-09-30"
    stored = json.loads(raw)
    assert stored["city"] == "Seattle"
    assert stored["weather"]["main"] == "Rain"


def test_save_mood_overwrite_default():
    redis_client = MagicMock()
    redis_client.get.return_value = json.dumps(
        {"date": "2026-09-30", "mood": "old", "city": "Seattle", "weather": {}}
    )

    entry = save_mood(
        redis_client,
        mood="new",
        city="Seattle",
        weather={"temp": 10},
        day="2026-09-30",
        overwrite=True,
    )
    assert entry["mood"] == "new"
    redis_client.set.assert_called_once()


def test_save_mood_reject_duplicate_when_overwrite_false():
    redis_client = MagicMock()
    redis_client.get.return_value = json.dumps(
        {"date": "2026-09-30", "mood": "old", "city": "Seattle", "weather": {}}
    )

    with pytest.raises(MoodError) as exc:
        save_mood(
            redis_client,
            mood="new",
            city="Seattle",
            weather={"temp": 10},
            day="2026-09-30",
            overwrite=False,
        )
    assert exc.value.status_code == 409


def test_get_mood_missing():
    redis_client = MagicMock()
    redis_client.get.return_value = None
    assert get_mood(redis_client, day="2026-09-30") is None


def test_list_moods_sorted():
    redis_client = MagicMock()
    redis_client.scan_iter.return_value = iter(
        ["moods:2026-09-29", "moods:2026-09-30"]
    )

    def _get(key):
        if key == "moods:2026-09-29":
            return json.dumps({"date": "2026-09-29", "mood": "meh"})
        return json.dumps({"date": "2026-09-30", "mood": "good"})

    redis_client.get.side_effect = _get
    rows = list_moods(redis_client)
    assert [r["date"] for r in rows] == ["2026-09-29", "2026-09-30"]
    redis_client.scan_iter.assert_called_once_with(match="moods:*", count=100)


def test_list_moods_filtered_by_anon_id():
    redis_client = MagicMock()
    redis_client.scan_iter.return_value = iter(
        ["moods:user-1:2026-09-29", "moods:user-1:2026-09-30"]
    )

    def _get(key):
        if key == "moods:user-1:2026-09-29":
            return json.dumps({"date": "2026-09-29", "mood": "meh"})
        return json.dumps({"date": "2026-09-30", "mood": "good"})

    redis_client.get.side_effect = _get
    rows = list_moods(redis_client, anon_id="user-1")
    assert [r["date"] for r in rows] == ["2026-09-29", "2026-09-30"]
    redis_client.scan_iter.assert_called_once_with(match="moods:user-1:*", count=100)
