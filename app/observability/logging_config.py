
import json
import logging
import os
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Format application logs as structured JSON."""

    def format(self, record):
        entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in (
            "event",
            "thread_id",
            "duration_ms",
            "status",
            "error_type",
        ):
            value = getattr(record, field, None)
            if value is not None:
                entry[field] = value

        if record.exc_info:
            entry["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(entry, ensure_ascii=False)


def configure_logging():
    """Configure JSON logging for the application."""

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
