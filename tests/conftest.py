import pytest

from app import create_app


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "OPENWEATHER_API_KEY": "test-key",
            "REDIS_URL": "redis://localhost:6379/15",
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
