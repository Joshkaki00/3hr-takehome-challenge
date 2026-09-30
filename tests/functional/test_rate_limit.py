from app import create_app


def test_rate_limit_returns_429(redis_client):
    app = create_app(
        {
            "TESTING": True,
            "OPENWEATHER_API_KEY": "test-key",
            "REDIS_CLIENT": redis_client,
            "RATELIMIT_ENABLED": True,
            "RATELIMIT_STORAGE_URI": "memory://",
            "RATELIMIT_DEFAULT": "2 per minute",
        }
    )
    client = app.test_client()

    assert client.get("/moods").status_code == 200
    assert client.get("/moods").status_code == 200
    limited = client.get("/moods")
    assert limited.status_code == 429


def test_health_exempt_from_rate_limit(redis_client):
    app = create_app(
        {
            "TESTING": True,
            "OPENWEATHER_API_KEY": "test-key",
            "REDIS_CLIENT": redis_client,
            "RATELIMIT_ENABLED": True,
            "RATELIMIT_STORAGE_URI": "memory://",
            "RATELIMIT_DEFAULT": "1 per minute",
        }
    )
    client = app.test_client()
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
