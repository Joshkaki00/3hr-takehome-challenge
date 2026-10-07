from unittest.mock import patch

from app.weather import WeatherError


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_ready_ok(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ready"
    assert body["redis"] is True


def test_ready_redis_down(client, redis_client):
    with patch.object(redis_client, "ping", side_effect=ConnectionError("down")):
        resp = client.get("/ready")
    assert resp.status_code == 503
    body = resp.get_json()
    assert body["status"] == "not_ready"
    assert body["redis"] is False


def test_weather_missing_city(client):
    resp = client.get("/weather")
    assert resp.status_code == 400
    assert "city" in resp.get_json()["error"].lower()


def test_weather_success(client):
    fake = {
        "city": "Seattle",
        "country": "US",
        "lat": 47.6,
        "lon": -122.3,
        "weather": {"temp": 12.0, "main": "Rain", "description": "light rain"},
    }
    with patch("app.routes.weather.weather_for_city", return_value=fake):
        resp = client.get("/weather?city=Seattle")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["city"] == "Seattle"
    assert body["weather"]["main"] == "Rain"


def test_weather_not_found(client):
    with patch(
        "app.routes.weather.weather_for_city",
        side_effect=WeatherError("city not found: Narnia", status_code=404),
    ):
        resp = client.get("/weather?city=Narnia")
    assert resp.status_code == 404


def test_post_mood_created(client, redis_client):
    fake_weather = {
        "city": "Seattle",
        "country": "US",
        "lat": 47.6,
        "lon": -122.3,
        "weather": {"temp": 12, "main": "Rain"},
    }
    payload = {"mood": "chill", "city": "Seattle", "date": "2026-09-30"}
    with patch("app.routes.weather.weather_for_city", return_value=fake_weather):
        resp = client.post("/moods", json=payload)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["mood"] == "chill"
    assert body["date"] == "2026-09-30"
    assert "anon_id" in body
    assert "X-Anon-Id" in resp.headers

    # Verify mood was stored in Redis
    anon_id = body["anon_id"]
    stored = redis_client.get(f"moods:{anon_id}:2026-09-30")
    assert stored is not None
    import json
    stored_data = json.loads(stored)
    assert stored_data["mood"] == "chill"


def test_post_mood_requires_mood(client):
    fake_weather = {
        "city": "Seattle",
        "country": "US",
        "lat": 47.6,
        "lon": -122.3,
        "weather": {"temp": 12, "main": "Rain"},
    }
    with patch("app.routes.weather.weather_for_city", return_value=fake_weather):
        resp = client.post(
            "/moods",
            json={"city": "Seattle", "date": "2026-09-30"},
        )
    assert resp.status_code == 400


def test_post_mood_requires_city(client):
    resp = client.post("/moods", json={"mood": "happy", "date": "2026-09-30"})
    assert resp.status_code == 400
    assert "city" in resp.get_json()["error"].lower()


def test_post_mood_with_anon_id_header(client, redis_client):
    fake_weather = {
        "city": "Seattle",
        "country": "US",
        "lat": 47.6,
        "lon": -122.3,
        "weather": {"temp": 12, "main": "Rain"},
    }
    payload = {"mood": "happy", "city": "Seattle"}
    with patch("app.routes.weather.weather_for_city", return_value=fake_weather):
        resp = client.post(
            "/moods", json=payload, headers={"X-Anon-Id": "user-123"}
        )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["anon_id"] == "user-123"
    assert resp.headers.get("X-Anon-Id") == "user-123"


def test_get_moods_empty(client):
    resp = client.get("/moods")
    assert resp.status_code == 200
    assert resp.get_json() == []
