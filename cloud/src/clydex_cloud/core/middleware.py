"""ASGI size/rate/TLS/concurrency protection and metadata-only request logs."""
import asyncio
import json
import logging
import threading
import time
import uuid
from starlette.exceptions import HTTPException


class RequestGuard:
    def __init__(self, app, settings):
        self.app, self.settings = app, settings
        self.buckets, self.lock = {}, threading.Lock()
        self.active = threading.BoundedSemaphore(16)
        self.auth_active = threading.BoundedSemaphore(2)
        self.logger = logging.getLogger('clydex.cloud.requests')

    async def error(self, send, status, code, request_id, retry=None):
        headers = [(b'content-type', b'application/json'), (b'x-request-id', request_id.encode()),
                   (b'cache-control', b'no-store')]
        if retry:
            headers.append((b'retry-after', str(retry).encode()))
        await send({'type': 'http.response.start', 'status': status, 'headers': headers})
        await send({'type': 'http.response.body', 'body': json.dumps({'error': {'code': code, 'request_id': request_id}}).encode()})

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            await send({'type': 'websocket.close', 'code': 1008})
            return
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        started, request_id = time.monotonic(), str(uuid.uuid4())
        scope.setdefault('state', {})['request_id'] = request_id
        headers = dict(scope['headers'])
        for field in (b'host', b'authorization', b'content-length', b'transfer-encoding'):
            if sum(k.lower() == field for k, _ in scope['headers']) > 1:
                return await self.error(send, 400, 'duplicate_header', request_id)
        if sum(len(k) + len(v) for k, v in scope['headers']) > 16384:
            return await self.error(send, 431, 'request_headers_limit', request_id)
        if self.settings.require_tls and scope.get('scheme') != 'https' and scope['path'] not in ('/healthz', '/readyz'):
            return await self.error(send, 400, 'tls_required', request_id)
        host = headers.get(b'host', b'').decode('ascii', 'ignore').split(':', 1)[0]
        if host != self.settings.public_host:
            return await self.error(send, 400, 'invalid_host', request_id)
        auth_route = scope['path'].startswith(('/v1/auth/', '/v1/devices/claims'))
        bucket = (scope.get('client', ('unknown',))[0], 'authentication' if auth_route else 'api')
        now = time.monotonic()
        with self.lock:
            if len(self.buckets) >= 4096 and bucket not in self.buckets:
                self.buckets = {k: v for k, v in self.buckets.items() if v[0] > now - 60}
            if len(self.buckets) >= 4096 and bucket not in self.buckets:
                permitted = False
            else:
                window, count = self.buckets.get(bucket, (now, 0))
                if window <= now - 60:
                    window, count = now, 0
                permitted = count < (8 if auth_route else self.settings.request_limit)
                self.buckets[bucket] = (window, count + 1)
        if not permitted:
            return await self.error(send, 429, 'rate_limited', request_id, 60)
        upload = scope['path'].endswith(('/documents', '/versions')) and scope['method'] == 'POST'
        limit = self.settings.max_file_bytes if upload else 256 * 1024
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            return await self.error(send, 400, 'invalid_content_length', request_id)
        if length < 0 or length > limit:
            return await self.error(send, 413, 'request_size_limit', request_id)
        if not self.active.acquire(blocking=False):
            return await self.error(send, 503, 'server_busy', request_id, 1)
        if auth_route and not self.auth_active.acquire(blocking=False):
            self.active.release()
            return await self.error(send, 503, 'authentication_busy', request_id, 1)
        total, status, sent = 0, 500, False
        async def bounded_receive():
            nonlocal total
            message = await receive()
            total += len(message.get('body', b''))
            if total > limit:
                raise RequestTooLarge()
            return message
        async def private_send(message):
            nonlocal status, sent
            if message['type'] == 'http.response.start':
                sent, status = True, message['status']
                message['headers'] += [(b'x-request-id', request_id.encode()), (b'cache-control', b'no-store'),
                                       (b'x-content-type-options', b'nosniff')]
            await send(message)
        try:
            await self.app(scope, bounded_receive, private_send)
        except RequestTooLarge:
            if not sent:
                await self.error(send, 413, 'request_size_limit', request_id)
        except (asyncio.CancelledError, ConnectionError):
            raise
        except Exception:
            if not sent:
                await self.error(send, 500, 'operation_failed', request_id)
        finally:
            self.active.release()
            if auth_route:
                self.auth_active.release()
            route = scope.get('route')
            self.logger.info(json.dumps(dict(request_id=request_id, method=scope['method'],
                route=getattr(route, 'path', 'unmatched'), status=status,
                duration_ms=round((time.monotonic() - started) * 1000, 2))))


class RequestTooLarge(HTTPException):
    def __init__(self):
        super().__init__(413, 'request_size_limit')
