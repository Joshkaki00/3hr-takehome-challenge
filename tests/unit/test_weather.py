from unittest.mock import MagicMock

import pytest

from app.weather import WeatherError, geocode_city, fetch_current_weather, weather_for_city


def test_geocode_requires_city():
    with pytest.raises(WeatherError) as exc:
        geocode_city("", "test-key")
    assert exc.value.status_code == 400


def test_geocode_requires_api_key():
    with pytest.raises(WeatherError) as exc:
        geocode_city("Seattle", "")
    assert exc.value.status_code == 500


def test_geocode_city_not_found():
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = []
    resp.raise_for_status.return_value = None
    session.get.return_value = resp

    with pytest.raises(WeatherError) as exc:
        geocode_city("Narnia", "test-key", session=session)
    assert exc.value.status_code == 404


def test_geocode_success():
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = [
        {"name": "Seattle", "lat": 47.6, "lon": -122.3, "country": "US"}
    ]
    resp.raise_for_status.return_value = None
    session.get.return_value = resp

    place = geocode_city("Seattle", "test-key", session=session)
    assert place["name"] == "Seattle"
    assert place["lat"] == 47.6
    assert place["lon"] == -122.3


def test_fetch_current_weather_success():
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "data": [
            {
                "temp": 18.5,
                "feels_like": 17.0,
                "humidity": 70,
                "weather": [{"main": "Clouds", "description": "broken clouds"}],
            }
        ]
    }
    resp.raise_for_status.return_value = None
    session.get.return_value = resp

    current = fetch_current_weather(47.6, -122.3, "test-key", session=session)
    assert current["temp"] == 18.5
    assert current["main"] == "Clouds"


def test_fetch_current_weather_service_down():
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = 503
    session.get.return_value = resp

    with pytest.raises(WeatherError) as exc:
        fetch_current_weather(47.6, -122.3, "test-key", session=session)
    assert exc.value.status_code == 502


def test_weather_for_city_combines_geo_and_current():
    session = MagicMock()

    geo_resp = MagicMock()
    geo_resp.status_code = 200
    geo_resp.json.return_value = [
        {"name": "Seattle", "lat": 47.6, "lon": -122.3, "country": "US"}
    ]
    geo_resp.raise_for_status.return_value = None

    wx_resp = MagicMock()
    wx_resp.status_code = 200
    wx_resp.json.return_value = {
        "data": [
            {
                "temp": 12.0,
                "feels_like": 11.0,
                "humidity": 80,
                "weather": [{"main": "Rain", "description": "light rain"}],
            }
        ]
    }
    wx_resp.raise_for_status.return_value = None

    session.get.side_effect = [geo_resp, wx_resp]

    result = weather_for_city("Seattle", "test-key", session=session)
    assert result["city"] == "Seattle"
    assert result["weather"]["main"] == "Rain"
    assert session.get.call_count == 2
