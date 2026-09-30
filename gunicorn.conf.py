"""Gunicorn production settings: bind + JSON structured logs."""

bind = "0.0.0.0:5000"
workers = 2
accesslog = "-"
errorlog = "-"
capture_output = True

# Unified JSON stream for access + error + app loggers.
# https://til.codeinthehole.com/posts/how-to-get-gunicorn-to-log-as-json/
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "rename_fields": {"asctime": "timestamp", "levelname": "level"},
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
    "loggers": {
        "gunicorn.error": {
            "level": "INFO",
            "handlers": [],
            "propagate": True,
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": [],
            "propagate": True,
        },
    },
}
