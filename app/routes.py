from flask import Blueprint, current_app, jsonify, request

from app import moods, weather

bp = Blueprint("api", __name__)


@bp.get("/health")
def health():
    redis_client = current_app.extensions.get("redis")
    redis_ok = False
    if redis_client is not None:
        try:
            redis_ok = redis_client.ping() is True
        except Exception:
            redis_ok = False
    return jsonify({"status": "ok", "redis": redis_ok})


@bp.get("/weather")
def get_weather():
    city = request.args.get("city", "")
    api_key = current_app.config.get("OPENWEATHER_API_KEY", "")
    try:
        data = weather.weather_for_city(city, api_key)
    except weather.WeatherError as err:
        return jsonify({"error": err.message}), err.status_code
    return jsonify(data)


@bp.post("/moods")
def post_mood():
    body = request.get_json(silent=True) or {}
    # redis client is injected on app for easy mocking in tests
    redis_client = current_app.extensions.get("redis")
    if redis_client is None:
        return jsonify({"error": "redis is not configured"}), 500
    try:
        entry = moods.save_mood(
            redis_client,
            mood=body.get("mood"),
            city=body.get("city"),
            weather=body.get("weather"),
            day=body.get("date"),
            overwrite=True,
        )
    except moods.MoodError as err:
        return jsonify({"error": err.message}), err.status_code
    return jsonify(entry), 201


@bp.get("/moods")
def get_moods():
    redis_client = current_app.extensions.get("redis")
    if redis_client is None:
        return jsonify({"error": "redis is not configured"}), 500
    return jsonify(moods.list_moods(redis_client))
