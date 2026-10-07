import uuid

from flask import Blueprint, current_app, jsonify, request

from app import moods, weather
from app.extensions import limiter

bp = Blueprint("api", __name__)


@bp.get("/health")
@limiter.exempt
def health():
    # Liveness only: process is up. Do not probe Redis here (restart storms).
    return jsonify({"status": "ok"})


@bp.get("/ready")
@limiter.exempt
def ready():
    # Readiness: can we serve traffic that needs Redis?
    redis_client = current_app.extensions.get("redis")
    redis_ok = False
    if redis_client is not None:
        try:
            redis_ok = redis_client.ping() is True
        except Exception:
            redis_ok = False
    payload = {
        "status": "ready" if redis_ok else "not_ready",
        "redis": redis_ok,
    }
    return jsonify(payload), (200 if redis_ok else 503)


@bp.get("/weather")
@limiter.limit("30 per minute")
def get_weather():
    city = request.args.get("city", "")
    api_key = current_app.config.get("OPENWEATHER_API_KEY", "")
    try:
        data = weather.weather_for_city(city, api_key)
    except weather.WeatherError as err:
        return jsonify({"error": err.message}), err.status_code
    return jsonify(data)


@bp.post("/moods")
@limiter.limit("20 per minute")
def post_mood():
    body = request.get_json(silent=True) or {}
    redis_client = current_app.extensions.get("redis")
    if redis_client is None:
        return jsonify({"error": "redis is not configured"}), 500

    # Get or create anonymous user ID
    anon_id = request.headers.get("X-Anon-Id", "").strip() or str(uuid.uuid4())

    # Fetch weather server-side based on city
    city = body.get("city", "").strip()
    if not city:
        return jsonify({"error": "city is required"}), 400

    api_key = current_app.config.get("OPENWEATHER_API_KEY", "")
    try:
        weather_data = weather.weather_for_city(city, api_key)
    except weather.WeatherError as err:
        return jsonify({"error": err.message}), err.status_code

    try:
        entry = moods.save_mood(
            redis_client,
            mood=body.get("mood"),
            city=city,
            weather=weather_data,
            day=body.get("date"),
            anon_id=anon_id,
            overwrite=True,
        )
    except moods.MoodError as err:
        return jsonify({"error": err.message}), err.status_code

    response = jsonify({**entry, "anon_id": anon_id})
    response.headers["X-Anon-Id"] = anon_id
    return response, 201


@bp.get("/moods")
def get_moods():
    redis_client = current_app.extensions.get("redis")
    if redis_client is None:
        return jsonify({"error": "redis is not configured"}), 500
    anon_id = request.headers.get("X-Anon-Id", "").strip() or None
    return jsonify(moods.list_moods(redis_client, anon_id))
