import json
import logging
from io import StringIO

from pythonjsonlogger.json import JsonFormatter


def test_json_formatter_emits_object():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    )
    logger = logging.getLogger("test.json")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info("hello_json")
    payload = json.loads(stream.getvalue().strip())
    assert payload["message"] == "hello_json"
    assert payload["level"] == "INFO"
    assert "timestamp" in payload
