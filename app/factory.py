import os

import redis
from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        OPENWEATHER_API_KEY=os.getenv("OPENWEATHER_API_KEY", ""),
        REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
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

    from app.routes import bp

    app.register_blueprint(bp)
    return app
