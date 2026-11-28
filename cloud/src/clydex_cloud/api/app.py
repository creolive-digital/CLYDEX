"""Independent versioned cloud HTTP application. No desktop/tool execution routes."""
from contextlib import asynccontextmanager
import base64
import hmac
from urllib.parse import quote

from fastapi import FastAPI, Depends, Header, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, TimeoutError as DatabaseTimeout
from starlette.exceptions import HTTPException

from clydex_cloud.api import contracts as dto, responses as output
from clydex_cloud.api.authentication import AuthenticationMiddleware
from clydex_cloud.core.config import Settings
from clydex_cloud.core.errors import CloudError
from clydex_cloud.core.middleware import RequestGuard
from clydex_cloud.core.runtime import Runtime
from clydex_cloud.repositories.schema import jobs, accounts


def create_app(settings: Settings | None = None, *, runtime=None) -> FastAPI:
    settings = settings or Settings.from_environment()
    from clydex_cloud.core.logging import configure
    configure()
    if runtime is not None and settings.environment != 'test':
        raise ValueError('Runtime injection is test-only.')
    runtime = runtime or Runtime(settings)

    @asynccontextmanager
    async def lifespan(app):
        if settings.inline_workers:
            runtime.worker.start(settings.inline_workers)
        try:
            yield
        finally:
            runtime.close()

    app = FastAPI(title='CLYDEX Cloud', version='0.5.0', lifespan=lifespan,
        responses={status: {'model': output.ErrorEnvelope} for status in (400, 401, 403, 404, 409, 413, 415, 422, 429, 503)},
        # JSON documentation stays local/authenticated; no external Swagger CDN.
        docs_url=None, redoc_url=None,
        openapi_url='/v1/openapi.json' if settings.docs_enabled else None)
    app.state.runtime = runtime
    app.add_middleware(AuthenticationMiddleware, authentication=runtime.authentication)
    app.add_middleware(RequestGuard, settings=settings)

    @app.exception_handler(CloudError)
    async def cloud_error(request, exc):
        return JSONResponse({'error': {'code': exc.code, **exc.metadata,
            'request_id': request.state.request_id}}, status_code=exc.status,
            headers={'Retry-After': str(exc.metadata['retry_after'])} if 'retry_after' in exc.metadata else {})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse({'error': {'code': 'validation_failed', 'request_id': request.state.request_id,
            'fields': [{'location': [str(x) for x in e['loc']], 'type': e['type']} for e in exc.errors()[:20]]}}, status_code=422)

    @app.exception_handler(IntegrityError)
    async def constraint_error(request, exc):
        return JSONResponse({'error': {'code': 'resource_conflict', 'request_id': request.state.request_id}}, status_code=409)

    @app.exception_handler(OperationalError)
    @app.exception_handler(DatabaseTimeout)
    async def data_unavailable(request, exc):
        return JSONResponse({'error': {'code': 'data_service_unavailable', 'request_id': request.state.request_id}},
                            status_code=503, headers={'Retry-After': '5'})

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse({'error': {'code': 'request_size_limit' if exc.status_code == 413 else 'http_error',
            'request_id': request.state.request_id}}, status_code=exc.status_code)

    def actor(request: Request):
        return request.state.principal

    @app.get('/healthz', response_model=output.Status)
    def health():
        return {'status': 'alive'}

    @app.get('/readyz', response_model=output.Status)
    def ready(response: Response):
        if not runtime.database.ready():
            response.status_code = 503
            return {'status': 'not_ready'}
        return {'status': 'ready'}

    @app.post('/v1/auth/register', response_model=output.Provisioned, status_code=201)
    def register(body: dto.Register):
        if not settings.registration_enabled:
            raise CloudError('registration_closed', 403)
        expected = base64.urlsafe_b64encode(settings.secret('registration.key')).decode().rstrip('=')
        invitation = body.invitation.get_secret_value()
        if not hmac.compare_digest(expected, invitation):
            raise CloudError('registration_unavailable', 403)
        return runtime.authentication.provision(body.login, body.password.get_secret_value(),
            invitation_digest=runtime.cipher.digest('invitation', invitation))

    @app.post('/v1/auth/login', response_model=output.Session)
    def login(body: dto.Login):
        return runtime.authentication.login(body.login, body.password.get_secret_value())

    @app.post('/v1/auth/refresh', response_model=output.Session)
    def refresh(body: dto.Refresh):
        return runtime.authentication.rotate(body.refresh_token.get_secret_value())

    @app.post('/v1/auth/logout', response_model=output.Flag)
    def logout(all_sessions: bool = False, principal=Depends(actor)):
        return runtime.authentication.logout(principal, all_sessions)

    @app.post('/v1/auth/recover', response_model=output.Recovered)
    def recover(body: dto.Recover):
        return runtime.authentication.recover(body.login, body.recovery_code.get_secret_value(), body.new_password.get_secret_value())

    @app.get('/v1/account', response_model=output.Account)
    def account(principal=Depends(actor)):
        with runtime.database.transaction() as c:
            row = c.execute(select(accounts).where(accounts.c.id == principal.owner_id)).mappings().one()
            return dict(id=principal.owner_id, **runtime.cipher.open(c, principal.owner_id, 'account', row['profile']))

    @app.get('/v1/status', response_model=output.Capabilities)
    def status(principal=Depends(actor)):
        return dict(database='simulated_test_repository' if runtime.database.simulated else 'sql_server',
            embedding_configured=runtime.embeddings.configured, vector_strategy='native_exact_only',
            preview_vector_indexes=False, formats='GET authenticated OpenAPI or local API reference',
            server_managed_encryption=True, e2ee=False)

    @app.get('/v1/devices', response_model=output.Items)
    def device_list(principal=Depends(actor)):
        principal.require('devices.manage')
        return {'items': runtime.devices.list(principal)}

    @app.post('/v1/devices/pairings', response_model=output.PairingResult, status_code=201)
    def pairing(body: dto.Pairing, principal=Depends(actor)):
        return runtime.devices.request_pairing(principal, body.model_dump(exclude={'scopes'}), body.scopes)

    @app.post('/v1/devices/pairings/{key}/approval', response_model=output.Flag)
    def pairing_approve(key: dto.Identifier, principal=Depends(actor)):
        return runtime.devices.approve(principal, key)

    @app.post('/v1/devices/claims', response_model=output.Session, status_code=201)
    def pairing_claim(body: dto.Claim):
        return runtime.devices.claim(body.pairing_token.get_secret_value())

    @app.delete('/v1/devices/{key}', response_model=output.Flag)
    def device_revoke(key: dto.Identifier, principal=Depends(actor)):
        return runtime.devices.revoke(principal, key)

    @app.post('/v1/devices/{key}/credentials', response_model=output.Session)
    def device_rotate(key: dto.Identifier, principal=Depends(actor)):
        return runtime.devices.rotate(principal, key)

    @app.get('/v1/collections', response_model=output.Items)
    def collection_list(principal=Depends(actor)):
        return runtime.vault.list_collections(principal)

    @app.post('/v1/collections', response_model=output.CollectionResult, status_code=201)
    def collection_create(body: dto.Collection, response: Response, principal=Depends(actor)):
        value = runtime.vault.create_collection(principal, body.model_dump())
        response.headers['Location'] = '/v1/collections/' + value['id']
        return value

    @app.delete('/v1/collections/{key}', response_model=output.Flag)
    def collection_delete(key: dto.Identifier, expected_revision: int = Query(ge=1), principal=Depends(actor)):
        return runtime.vault.delete_collection(principal, key, expected_revision)

    @app.get('/v1/documents', response_model=output.Items)
    def document_list(collection_id: dto.Identifier | None = None, principal=Depends(actor)):
        return runtime.vault.list_documents(principal, collection_id)

    @app.post('/v1/collections/{key}/documents', response_model=output.UploadResult, status_code=201)
    async def document_upload(key: dto.Identifier, request: Request, response: Response,
            name: str = Query(min_length=1, max_length=180),
            idempotency_key: dto.Identifier = Header(alias='Idempotency-Key'), principal=Depends(actor)):
        from anyio import to_thread
        data = await request.body()
        value = await to_thread.run_sync(lambda: runtime.vault.upload(principal, key, name, data, idempotency_key))
        response.headers['Location'] = '/v1/documents/' + value['document_id']
        return value

    @app.post('/v1/documents/{key}/versions', response_model=output.UploadResult, status_code=201)
    async def document_version(key: dto.Identifier, request: Request, collection_id: dto.Identifier,
            name: str = Query(min_length=1, max_length=180), expected_revision: int = Query(ge=1),
            idempotency_key: dto.Identifier = Header(alias='Idempotency-Key'), principal=Depends(actor)):
        from anyio import to_thread
        data = await request.body()
        return await to_thread.run_sync(lambda: runtime.vault.upload(principal, collection_id, name, data,
            idempotency_key, document_id=key, expected_revision=expected_revision))

    @app.get('/v1/documents/{key}/versions', response_model=output.Items)
    def version_list(key: dto.Identifier, principal=Depends(actor)):
        return runtime.vault.list_versions(principal, key)

    @app.get('/v1/documents/{key}/content')
    def document_content(key: dto.Identifier, version: int | None = Query(default=None, ge=1), principal=Depends(actor)):
        metadata, content = runtime.vault.content(principal, key, version)
        return Response(content=content, media_type='application/octet-stream', headers={
            'Content-Disposition': "attachment; filename*=UTF-8''" + quote(metadata['name'], safe=''),
            'X-Content-SHA256': metadata['sha256']})

    @app.delete('/v1/documents/{key}', response_model=output.Flag)
    def document_delete(key: dto.Identifier, expected_revision: int = Query(ge=1), principal=Depends(actor)):
        return runtime.vault.delete_document(principal, key, expected_revision)

    @app.post('/v1/documents/{key}/processing', response_model=output.JobResult, status_code=202)
    def document_reprocess(key: dto.Identifier, expected_revision: int = Query(ge=1), principal=Depends(actor)):
        return runtime.vault.reprocess(principal, key, expected_revision)

    @app.post('/v1/notes', response_model=output.UploadResult, status_code=201)
    def note_create(body: dto.Note, principal=Depends(actor)):
        return runtime.vault.upload(principal, body.collection_id, 'note.md', body.text.encode('utf-8'), body.operation_id,
            source='personal_note', title=body.title)

    @app.get('/v1/documents/{key}/excerpts', response_model=output.Items)
    def document_excerpts(key: dto.Identifier, offset: int = Query(default=0, ge=0, le=2000),
            limit: int = Query(default=10, ge=1, le=20), principal=Depends(actor)):
        from clydex_cloud.repositories.schema import passages, documents
        from clydex.knowledge.models import citation_id
        principal.require('vault.read')
        with runtime.database.transaction() as c:
            document = runtime.vault.owned(c, documents, principal.owner_id, key, live=True)
            profile = runtime.cipher.open(c, principal.owner_id, 'document:' + key, document['profile'])
            rows = c.execute(select(passages).where(passages.c.owner_id == principal.owner_id,
                passages.c.document_id == key, passages.c.version == document['current_version'],
                passages.c.ordinal >= offset).order_by(passages.c.ordinal).limit(limit + 1)).mappings().all()
            values = []
            for row in rows[:limit]:
                passage = runtime.cipher.open(c, principal.owner_id, 'chunk:' + row['id'], row['payload'])
                values.append(dict(citation_id=citation_id(key, row['version'], row['ordinal']), document_id=key,
                    version=row['version'], revision=document['revision'], ordinal=row['ordinal'],
                    name=profile['name'], location=passage['location'], excerpt=passage['text']))
            return dict(items=values, truncated=len(rows) > limit)

    @app.get('/v1/jobs', response_model=output.Items)
    def job_list(principal=Depends(actor)):
        principal.require('vault.read')
        with runtime.database.transaction() as c:
            rows = c.execute(select(jobs.c.id, jobs.c.document_id, jobs.c.version, jobs.c.status,
                jobs.c.error_code, jobs.c.attempts, jobs.c.created_at).where(jobs.c.owner_id == principal.owner_id)
                .order_by(jobs.c.created_at.desc()).limit(100)).mappings()
            return {'items': [dict(row) for row in rows]}

    @app.post('/v1/knowledge/search', response_model=output.SearchResult)
    def search(body: dto.Search, principal=Depends(actor)):
        return runtime.retrieval.search(principal, **body.model_dump())

    @app.get('/v1/sync/preferences', response_model=dto.SyncPreferences)
    def sync_preferences(principal=Depends(actor)):
        principal.require('sync.read')
        with runtime.database.transaction() as c:
            return runtime.synchronization.preference(c, principal.owner_id)

    @app.put('/v1/sync/preferences', response_model=dto.SyncPreferences)
    def sync_configure(body: dto.SyncPreferences, principal=Depends(actor)):
        return runtime.synchronization.configure(principal, body.model_dump())

    @app.post('/v1/sync/operations', response_model=output.SyncResult)
    def sync_push(body: dto.SyncBatch, principal=Depends(actor)):
        return runtime.synchronization.push(principal, [v.model_dump() for v in body.operations])

    @app.get('/v1/sync/changes', response_model=output.Changes)
    def sync_pull(cursor: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500), principal=Depends(actor)):
        return runtime.synchronization.pull(principal, cursor, limit)

    @app.get('/v1/storage/usage', response_model=output.Usage)
    def storage_usage(principal=Depends(actor)):
        principal.require('vault.read')
        return runtime.vault.usage(principal)

    from fastapi.openapi.utils import get_openapi
    def contract():
        if app.openapi_schema is None:
            document = get_openapi(title=app.title, version=app.version, routes=app.routes)
            document.setdefault('components', {}).setdefault('securitySchemes', {})['cloudBearer'] = {
                'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'opaque short-lived CLYDEX access token'}
            public = {'/healthz', '/readyz', '/v1/auth/register', '/v1/auth/login', '/v1/auth/refresh', '/v1/auth/recover', '/v1/devices/claims'}
            for path, methods in document['paths'].items():
                for method, definition in methods.items():
                    if method in ('get', 'post', 'put', 'delete', 'patch'):
                        definition['security'] = [] if path in public else [{'cloudBearer': []}]
            app.openapi_schema = document
        return app.openapi_schema
    app.openapi = contract
    return app
