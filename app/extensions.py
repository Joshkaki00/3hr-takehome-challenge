"""Shared Flask extensions (initialized in create_app)."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Defaults come from app.config RATELIMIT_* (set in create_app).
# Redis URI in prod so gunicorn workers share counters.
# https://flask-limiter.readthedocs.io/en/stable/
limiter = Limiter(
    key_func=get_remote_address,
    strategy="fixed-window",
)
