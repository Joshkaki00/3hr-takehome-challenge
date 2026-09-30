import os

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        OPENWEATHER_API_KEY=os.getenv("OPENWEATHER_API_KEY", ""),
        REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )
    if test_config is not None:
        app.config.update(test_config)

    from app.routes import bp

    app.register_blueprint(bp)
    return app
