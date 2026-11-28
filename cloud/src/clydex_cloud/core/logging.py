"""One JSON stdout logger for allowlisted request metadata; no body/trace logging."""
import logging
import sys


def configure():
    logger = logging.getLogger('clydex.cloud.requests')
    if not any(getattr(h, '_clydex_request_metadata', False) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(message)s'))
        handler._clydex_request_metadata = True
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
