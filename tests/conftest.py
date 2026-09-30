from unittest.mock import MagicMock

import pytest

from app import create_app


@pytest.fixture
def redis_client():
    client = MagicMock()
    client.ping.return_value = True
    client.get.return_value = None
    client.keys.return_value = []
    return client


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
