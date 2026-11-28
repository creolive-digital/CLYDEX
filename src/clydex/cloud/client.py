"""Bounded cloud REST client sharing the cancellation-aware provider transport.

Access/refresh credentials live in RAM only, never frontend state or DPAPI sync.
No redirects, cookie jar, proxy inheritance or automatic retries of effects.
"""
from dataclasses import dataclass
import json
import re
from urllib.parse import urlsplit

from clydex.core.contracts import canonical_json
from clydex.providers.transport import HTTPTransport


class CloudFailure(RuntimeError):
    def __init__(self, code, status=0):
        self.code, self.status = code, status
        super().__init__('Cloud request failed: ' + code)


@dataclass(frozen=True)
class CloudConfig:
    endpoint: str = ''
    enabled: bool = False

    def __post_init__(self):
        if type(self.enabled) is not bool or not isinstance(self.endpoint, str):
            raise ValueError('Invalid cloud configuration.')
        if not self.endpoint:
            if self.enabled:
                raise ValueError('Configure an HTTPS endpoint before enabling cloud.')
            return
        value = urlsplit(self.endpoint)
        if (len(self.endpoint) > 500 or value.scheme != 'https' or not value.hostname or value.path not in ('', '/')
                or value.username is not None or value.password is not None or value.query or value.fragment
                or any(c.isspace() for c in self.endpoint)):
            raise ValueError('Cloud endpoint must be an HTTPS origin without credentials or paths.')


class CloudClient:
    def __init__(self, config=CloudConfig(), *, transport=None):
        self.config, self.transport = config, transport or HTTPTransport()
        self.access = self.refresh = self.account_id = ''
        self.status = 'disabled' if not config.enabled else 'signed_out'

    def forget(self):
        self.access = self.refresh = self.account_id = ''
        self.status = 'signed_out' if self.config.enabled else 'disabled'

    def request(self, method, path, payload, cancel, *, authenticated=True, raw=None, operation_id=None):
        if not self.config.enabled:
            raise CloudFailure('disabled')
        if not path.startswith('/v1/') or any(x in path for x in ('\r', '\n', '#')):
            raise ValueError('Invalid internal cloud route.')
        if authenticated and not self.access:
            raise CloudFailure('signed_out', 401)
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        if authenticated:
            headers['Authorization'] = 'Bearer ' + self.access
        if operation_id:
            from clydex.synchronization.contracts import identifier
            headers['Idempotency-Key'] = identifier(operation_id)
        body = raw if raw is not None else (canonical_json(payload).encode() if payload is not None else None)
        if body is not None and len(body) > (10 * 1024 * 1024 if raw is not None else 256 * 1024):
            raise ValueError('Cloud request exceeds its size limit.')
        if raw is not None:
            headers['Content-Type'] = 'application/octet-stream'
        response = self.transport.exchange(method, self.config.endpoint.rstrip('/') + path,
            headers, body, cancel, 30, 2 * 1024 * 1024)
        if cancel.is_set():
            from clydex.core.errors import Cancelled
            raise Cancelled('Cloud response canceled; remote effects may already have completed.')
        try:
            value = json.loads(response.body)
        except (ValueError, UnicodeError):
            raise CloudFailure('invalid_response', response.status) from None
        if not 200 <= response.status < 300:
            if response.status in (401, 403):
                self.forget()
            code = value.get('error', {}).get('code', '') if isinstance(value, dict) else ''
            raise CloudFailure(code if isinstance(code, str) and re.fullmatch('[a-z_]{1,80}', code) else 'service_error', response.status)
        if not isinstance(value, dict):
            raise CloudFailure('invalid_response')
        return value

    def login(self, login, password, cancel):
        self.forget()
        return self._tokens(self.request('POST', '/v1/auth/login', {'login': login, 'password': password}, cancel, authenticated=False))

    def rotate(self, cancel):
        if not self.refresh:
            raise CloudFailure('signed_out', 401)
        credential = self.refresh
        # Ambiguous timeout after rotation requires login; never replay an old token.
        self.forget()
        return self._tokens(self.request('POST', '/v1/auth/refresh', {'refresh_token': credential}, cancel, authenticated=False))

    def _tokens(self, value):
        from clydex.synchronization.contracts import identifier
        try:
            identifier(value['account_id'])
            for key, prefix in (('access_token', 'clxa.'), ('refresh_token', 'clxr.')):
                token = value[key]
                if not isinstance(token, str) or not token.startswith(prefix) or not 70 <= len(token) <= 250:
                    raise ValueError()
        except (KeyError, ValueError, TypeError):
            self.forget()
            raise CloudFailure('invalid_session') from None
        self.access, self.refresh, self.account_id = value['access_token'], value['refresh_token'], value['account_id']
        self.status = 'authenticated'
        return {'authenticated': True, 'account_id': self.account_id, 'expires_in': value['expires_in']}
