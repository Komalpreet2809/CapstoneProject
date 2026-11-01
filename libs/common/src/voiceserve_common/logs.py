"""Structured JSON logs on stdout, masked before they are written.

Every record becomes one JSON object: timestamp, level, service, logger, message, plus any
`extra=` fields. Uvicorn's loggers are routed through the same handler so access logs (which
contain paths and query strings) are masked too.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from voiceserve_common.masking import mask_text, mask_value

# Attributes every LogRecord has; anything else on a record came from `extra=`.
_STANDARD_ATTRS = frozenset(vars(logging.makeLogRecord({}))) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "service": self.service,
            "logger": record.name,
            "msg": mask_text(record.getMessage()),
        }
        extras = {k: v for k, v in vars(record).items() if k not in _STANDARD_ATTRS}
        for key, value in mask_value(extras).items():
            payload.setdefault(key, value)
        if record.exc_info:
            payload["exc"] = mask_text(self.formatException(record.exc_info))
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(service: str, level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
