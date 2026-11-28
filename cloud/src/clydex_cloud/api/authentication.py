"""Authentication is enforced before protected routing/body handling."""
from starlette.responses import JSONResponse
from anyio import to_thread

from clydex_cloud.core.errors import CloudError

PUBLIC = frozenset(('/healthz', '/readyz', '/v1/auth/register', '/v1/auth/login',
                    '/v1/auth/refresh', '/v1/auth/recover', '/v1/devices/claims'))


class AuthenticationMiddleware:
    def __init__(self, app, authentication):
        self.app, self.auth = app, authentication

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'] in PUBLIC:
            return await self.app(scope, receive, send)
        try:
            authorization = dict(scope['headers']).get(b'authorization', b'').decode('ascii')
            if not authorization.startswith('Bearer ') or len(authorization) > 300:
                raise CloudError('authentication_required', 401)
            actor = await to_thread.run_sync(self.auth.authenticate, authorization[7:])
            scope.setdefault('state', {})['principal'] = actor
        except (CloudError, UnicodeError) as exc:
            response = JSONResponse({'error': {'code': exc.code if isinstance(exc, CloudError) else 'authentication_required',
                'request_id': scope.get('state', {}).get('request_id', '')}}, status_code=exc.status if isinstance(exc, CloudError) else 401)
            return await response(scope, receive, send)
        except Exception:
            return await JSONResponse({'error': {'code': 'authentication_unavailable'}}, status_code=503)(scope, receive, send)
        return await self.app(scope, receive, send)
