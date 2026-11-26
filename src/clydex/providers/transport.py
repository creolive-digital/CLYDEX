"""Direct TLS HTTP transport, bounded streaming and cooperative cancellation.

No environment proxies, redirects, cookies or automatic retries. The watchdog
interrupts an established socket on total deadline/cancel; DNS/connect remain
subject to the configured socket timeout. No worker continues a request afterward.
"""
import http.client
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit

from clydex.core.errors import Cancelled
from clydex.providers.base import ProviderFailure


class HTTPTransport:
    def request(self, method: str, url: str, headers: dict, body: bytes | None,
                cancel, timeout: float, limit: int, receive=None) -> bytes:
        if cancel.is_set():
            raise Cancelled('Request canceled before transmission.')
        parts = urlsplit(url)
        if parts.scheme not in ('https', 'http') or not parts.hostname:
            raise ProviderFailure('configuration')
        if parts.scheme == 'http' and parts.hostname not in ('127.0.0.1', '::1'):
            raise ProviderFailure('insecure_endpoint')
        connection = (http.client.HTTPSConnection(parts.hostname, parts.port, timeout=timeout,
                                                  context=ssl.create_default_context())
                      if parts.scheme == 'https' else
                      http.client.HTTPConnection(parts.hostname, parts.port, timeout=timeout))
        connection.auto_open = 0
        finished = threading.Event()
        timed_out = threading.Event()
        deadline = time.monotonic() + timeout
        owned_socket, response = None, None

        def watch():
            while not finished.wait(.02):
                if cancel.is_set() or time.monotonic() >= deadline:
                    timed_out.set()
                    active_socket = connection.sock or owned_socket
                    if active_socket:
                        try:
                            active_socket.shutdown(socket.SHUT_RDWR)
                        except OSError:
                            pass
                    connection.close()
                    return
        watchdog = threading.Thread(target=watch, name='clydex-http-deadline', daemon=True)
        watchdog.start()
        try:
            connection.connect()
            owned_socket = connection.sock
            if cancel.is_set():
                raise Cancelled('Request canceled before transmission.')
            if timed_out.is_set():
                raise ProviderFailure('timeout')
            connection.request(method, (parts.path or '/') + ('?' + parts.query if parts.query else ''),
                               body=body, headers=headers)
            response = connection.getresponse()
            if response.status != 200:
                kind = {401: 'authentication', 403: 'authentication', 404: 'model_unavailable',
                        429: 'rate_limit', 400: 'invalid_request'}.get(response.status, 'service_error')
                raise ProviderFailure(kind, response.status)
            total, result = 0, bytearray()
            while True:
                if cancel.is_set():
                    raise Cancelled('Request canceled.')
                if timed_out.is_set():
                    raise ProviderFailure('timeout')
                chunk = response.read1(4096)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    raise ProviderFailure('response_limit')
                if receive:
                    receive(chunk)
                else:
                    result.extend(chunk)
            if cancel.is_set():
                raise Cancelled('Request canceled.')
            if timed_out.is_set():
                raise ProviderFailure('timeout')
            return bytes(result)
        except (OSError, http.client.HTTPException, ValueError) as exc:
            if cancel.is_set():
                raise Cancelled('Request canceled.') from exc
            raise ProviderFailure('timeout' if timed_out.is_set() or isinstance(exc, TimeoutError)
                                  else 'network') from exc
        finally:
            finished.set()
            if response:
                response.close()
            connection.close()
            watchdog.join()
