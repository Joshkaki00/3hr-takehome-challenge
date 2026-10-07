import redis
import pytest

from app import create_app


@pytest.fixture(scope="session")
def redis_url():
    """Redis URL for tests; uses real Redis on localhost."""
    return "redis://localhost:6380/1"  # db 1 for tests, db 0 for dev


@pytest.fixture
def redis_client(redis_url):
    """Real Redis client for each test; cleaned up after."""
    client = redis.Redis.from_url(
        redis_url,
        decode_responses=True,
        protocol=2,
    )
    # Verify Redis is running
    try:
        client.ping()
    except redis.ConnectionError:
        pytest.skip("Redis not running on localhost:6380")

    yield client

    # Cleanup after each test
    client.flushdb()


@pytest.fixture
def app(redis_client):
    application = create_app(
        {
            "TESTING": True,
            "OPENWEATHER_API_KEY": "test-key",
            "REDIS_CLIENT": redis_client,
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
