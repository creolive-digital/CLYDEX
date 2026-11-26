"""Rotating JSON diagnostics with an allowlist, not heuristic secret filtering."""
from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class SafeFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Arbitrary messages, exception args/tracebacks and custom extras are private.
        return json.dumps({
            'time': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'event': record.msg if record.msg in ('core_started', 'core_stopped', 'operation_failed',
                                                  'audit_failed', 'worker_failed') else 'diagnostic',
            'error_type': type(record.exc_info[1]).__name__ if record.exc_info else None,
        })


def configure_logging(directory: Path) -> logging.Logger:
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('clydex')
    logger.setLevel(logging.INFO)
    logger.propagate = False
    filename = str((directory / 'application.log').resolve())
    for handler in list(logger.handlers):
        if getattr(handler, 'baseFilename', None) == filename:
            return logger
        logger.removeHandler(handler)
        handler.close()
    handler = RotatingFileHandler(filename, maxBytes=1_048_576, backupCount=3, encoding='utf-8')
    handler.setFormatter(SafeFormatter())
    logger.addHandler(handler)
    return logger
