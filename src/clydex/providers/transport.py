"""Bounded HTTP/TLS with cancel-aware nonblocking socket I/O.

HTTP framing stays in stdlib http.client. All connect/handshake/send/read waits
poll cancellation/deadline on the owning thread; no cross-thread socket close.
Native DNS resolution can delay completion and never outlives Core ownership.
"""
import errno
import http.client
import io
import select
import socket
import ssl
import time
from urllib.parse import urlsplit

from clydex.core.errors import Cancelled
from clydex.providers.base import ProviderFailure


def _check(cancel, deadline):
    if cancel.is_set():
        raise Cancelled('Provider request canceled.')
    if time.monotonic() >= deadline:
        raise ProviderFailure('timeout')


def _wait(stream, reading, cancel, deadline):
    while True:
        _check(cancel, deadline)
        ready = select.select([stream] if reading else [], [] if reading else [stream], [stream],
                              min(.02, max(0, deadline - time.monotonic())))
        if ready[0] or ready[1] or ready[2]:
            _check(cancel, deadline)
            return


class _SocketReader(io.RawIOBase):
    def __init__(self, adapter):
        super().__init__()
        self.adapter = adapter

    def readable(self):
        return True

    def readinto(self, buffer):
        data = self.adapter.receive(min(len(buffer), 4096))
        buffer[:len(data)] = data
        return len(data)


class _SocketAdapter:
    """http.client may release this facade; request() alone owns the real socket."""
    def __init__(self, stream, cancel, deadline, limit):
        self.stream, self.cancel, self.deadline, self.limit = stream, cancel, deadline, limit
        self.received = 0

    def makefile(self, mode):
        if mode != 'rb':
            raise ValueError('Only response reads are supported.')
        return io.BufferedReader(_SocketReader(self), buffer_size=4096)

    def close(self):
        # HTTP/1.0 releases the facade while its response still owns a reader.
        # Physical ownership belongs to the synchronous transport finally block.
        pass

    def sendall(self, data):
        view = memoryview(data)
        while view:
            _check(self.cancel, self.deadline)
            try:
                count = self.stream.send(view)
                if count <= 0:
                    raise ConnectionError('Connection ended during transmission.')
                view = view[count:]
            except ssl.SSLWantReadError:
                _wait(self.stream, True, self.cancel, self.deadline)
            except (ssl.SSLWantWriteError, BlockingIOError):
                _wait(self.stream, False, self.cancel, self.deadline)

    def receive(self, size):
        while True:
            _check(self.cancel, self.deadline)
            try:
                data = self.stream.recv(size)
                self.received += len(data)
                if self.received > self.limit + 65536:
                    raise ProviderFailure('response_limit')
                return data
            except ssl.SSLWantWriteError:
                _wait(self.stream, False, self.cancel, self.deadline)
            except (ssl.SSLWantReadError, BlockingIOError):
                _wait(self.stream, True, self.cancel, self.deadline)


class HTTPTransport:
    def _connect_socket(self, parts, cancel, deadline):
        port = parts.port or (443 if parts.scheme == 'https' else 80)
        # OS DNS may not be interruptible. No request follows an expired result.
        addresses = socket.getaddrinfo(parts.hostname, port, type=socket.SOCK_STREAM)
        last = None
        for family, kind, protocol, _, address in addresses:
            _check(cancel, deadline)
            stream = socket.socket(family, kind, protocol)
            try:
                stream.setblocking(False)
                code = stream.connect_ex(address)
                pending = {0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EALREADY, 10035, 10036, 10037}
                if code not in pending:
                    raise OSError(code, 'Connection unavailable.')
                if code:
                    _wait(stream, False, cancel, deadline)
                    error = stream.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                    if error:
                        raise OSError(error, 'Connection unavailable.')
                if parts.scheme == 'https':
                    context = ssl.create_default_context()
                    stream = context.wrap_socket(stream, server_hostname=parts.hostname, do_handshake_on_connect=False)
                    stream.setblocking(False)
                    while True:
                        _check(cancel, deadline)
                        try:
                            stream.do_handshake()
                            break
                        except ssl.SSLWantReadError:
                            _wait(stream, True, cancel, deadline)
                        except ssl.SSLWantWriteError:
                            _wait(stream, False, cancel, deadline)
                _check(cancel, deadline)
                return stream
            except BaseException as exc:
                stream.close()
                if not isinstance(exc, OSError):
                    raise
                last = exc
        raise last or ConnectionError('No endpoint address available.')

    def request(self, method: str, url: str, headers: dict, body: bytes | None,
                cancel, timeout: float, limit: int, receive=None) -> bytes:
        deadline = time.monotonic() + timeout
        _check(cancel, deadline)
        parts = urlsplit(url)
        if parts.scheme not in ('https', 'http') or not parts.hostname:
            raise ProviderFailure('configuration')
        if parts.scheme == 'http' and parts.hostname not in ('127.0.0.1', '::1'):
            raise ProviderFailure('insecure_endpoint')
        connection = http.client.HTTPConnection(parts.hostname, parts.port)
        connection.auto_open = 0
        stream, response = None, None
        try:
            stream = self._connect_socket(parts, cancel, deadline)
            _check(cancel, deadline)
            connection.sock = _SocketAdapter(stream, cancel, deadline, limit)
            connection.request(method, (parts.path or '/') + ('?' + parts.query if parts.query else ''),
                               body=body, headers=headers)
            response = connection.getresponse()
            if response.status != 200:
                kind = {401: 'authentication', 403: 'authentication', 404: 'model_unavailable',
                        429: 'rate_limit', 400: 'invalid_request'}.get(response.status, 'service_error')
                raise ProviderFailure(kind, response.status)
            total, result = 0, bytearray()
            while True:
                _check(cancel, deadline)
                chunk = response.read1(4096)
                if not chunk:
                    if response.length not in (None, 0):
                        raise ProviderFailure('incomplete_response')
                    break
                total += len(chunk)
                if total > limit:
                    raise ProviderFailure('response_limit')
                if receive:
                    receive(chunk)
                else:
                    result.extend(chunk)
            _check(cancel, deadline)
            return bytes(result)
        except (OSError, http.client.HTTPException, ValueError) as exc:
            _check(cancel, deadline)
            raise ProviderFailure('network') from exc
        finally:
            if response:
                response.close()
            connection.close()
            if stream:
                stream.close()
