import logging
import os
from logging.config import dictConfig

import redis
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.extensions import limiter


def _configure_json_logging():
    """Structured JSON logs for local `flask run` too (gunicorn uses conf)."""
    if getattr(_configure_json_logging, "_done", False):
        return
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.json.JsonFormatter",
                    "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
                    "rename_fields": {
                        "asctime": "timestamp",
                        "levelname": "level",
                    },
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "json",
                },
            },
            "root": {"level": "INFO", "handlers": ["stdout"]},
        }
    )
    _configure_json_logging._done = True


def create_app(test_config=None):
    if not (test_config or {}).get("TESTING"):
        _configure_json_logging()

    app = Flask(__name__)
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_password = os.getenv("REDIS_PASSWORD", "")

    # Inject REDIS_PASSWORD into URL only for non-localhost (Compose environment).
    # Dev (localhost:6380) runs without auth. Compose (service name 'redis') uses REDIS_PASSWORD.
    if redis_password and "://" in redis_url and "@" not in redis_url and "localhost" not in redis_url:
        # redis://redis:6379/0 -> redis://:password@redis:6379/0 (Compose)
        scheme_end = redis_url.find("://") + 3
        rest = redis_url[scheme_end:]
        redis_url = f"{redis_url[:scheme_end]}:{redis_password}@{rest}"

    app.config.from_mapping(
        OPENWEATHER_API_KEY=os.getenv("OPENWEATHER_API_KEY", ""),
        REDIS_URL=redis_url,
        # How many reverse proxies set X-Forwarded-* (0 = no ProxyFix).
        # https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/
        PROXY_COUNT=int(os.getenv("PROXY_COUNT", "0")),
        # Rate limits (Flask-Limiter). Redis URI shared across gunicorn workers.
        # https://flask-limiter.readthedocs.io/en/stable/
        RATELIMIT_DEFAULT=os.getenv("RATELIMIT_DEFAULT", "60 per minute"),
        RATELIMIT_STORAGE_URI=redis_url,
        RATELIMIT_HEADERS_ENABLED=True,
    )

    injected_redis = None
    if test_config is not None:
        injected_redis = test_config.get("REDIS_CLIENT")
        app.config.update(
            {k: v for k, v in test_config.items() if k != "REDIS_CLIENT"}
        )

    # Shared client on the app. decode_responses keeps mood JSON as str.
    # protocol=2 avoids RESP3 HELLO issues with older Redis servers.
    if injected_redis is not None:
        app.extensions["redis"] = injected_redis
    else:
        app.extensions["redis"] = redis.Redis.from_url(
            app.config["REDIS_URL"],
            decode_responses=True,
            protocol=2,
            socket_connect_timeout=2,
            socket_timeout=2,
            health_check_interval=30,
        )

    proxy_count = int(app.config.get("PROXY_COUNT", 0) or 0)
    if proxy_count > 0:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=proxy_count,
            x_proto=proxy_count,
            x_host=proxy_count,
            x_prefix=proxy_count,
        )

    # Tests: in-memory limiter (or disabled). Prod: Redis so workers share state.
    if app.config.get("TESTING"):
        app.config.setdefault("RATELIMIT_STORAGE_URI", "memory://")
        app.config.setdefault("RATELIMIT_ENABLED", False)
    limiter.init_app(app)

    from app.routes import bp

    app.register_blueprint(bp)
    logging.getLogger(__name__).info("app_created")
    return app
