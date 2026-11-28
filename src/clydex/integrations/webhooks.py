"""Authenticated event contract for trusted local ingress adapters, no listener."""
import hashlib
import hmac
import json
import time


def verify_event(body, timestamp, signature, secret, *, now=None):
    now = time.time() if now is None else now
    if (type(body) is not bytes or len(body) > 16384 or type(timestamp) is not str
            or not timestamp.isdigit() or abs(now - int(timestamp)) > 300
            or type(signature) is not str or not signature.startswith('sha256=')
            or type(secret) is not str or len(secret) < 32):
        raise ValueError('Webhook authentication failed.')
    expected = 'sha256=' + hmac.new(secret.encode('utf-8'), timestamp.encode('ascii') + b'.' + body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError('Webhook authentication failed.')
    value = json.loads(body)
    if (type(value) is not dict or set(value) != {'event_id', 'source', 'kind'}
            or any(type(v) is not str or not 1 <= len(v) <= 200 for v in value.values())
            or value['kind'] != 'webhook'):
        raise ValueError('Unsupported webhook envelope.')
    return value
