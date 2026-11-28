"""Actual Windows WebView2 with real cloud routes and synthetic SQL simulation.

No private data, public network, models, microphone or speaker. The dependency
adapter calls the real FastAPI application in-process. Native picker gestures,
TLS/VPS/SQL Server and physical lock are separate acceptance gates.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'cloud/src'))


def main(output, desktop_site):
    import site
    if desktop_site:
        site.addsitedir(str(desktop_site))
    import os
    import webview
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, event
    from sqlalchemy.pool import StaticPool
    from clydex_cloud.api.app import create_app
    from clydex_cloud.core.config import Settings
    from clydex_cloud.core.encryption import VaultCipher
    from clydex_cloud.core.runtime import Runtime
    from clydex_cloud.repositories.database import Database
    from clydex_cloud.repositories.migrate import migrate
    from clydex.core.application import CoreApplication
    from clydex.core.config import AppConfig, RuntimePaths
    from clydex.desktop.hud import HudBridge, HudService
    from clydex.desktop.studio import Studio
    from clydex.providers.transport import HTTPResult
    output.mkdir(parents=True, exist_ok=True)
    result = dict(kind='Actual Windows WebView2; real FastAPI in-process; synthetic SQLite SQL-repository simulation', passed=False,
                  no_external_network=True, no_audio_or_models=True)
    with tempfile.TemporaryDirectory(prefix='clydex-phase05-native-') as directory:
        base = Path(directory)
        settings = Settings(base / 'server', base / 'keys', environment='test', require_tls=False)
        engine = create_engine('sqlite+pysqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
        @event.listens_for(engine, 'connect')
        def foreign_keys(connection, record):
            connection.execute('PRAGMA foreign_keys=ON')
        database = Database('', engine=engine, test_only=True)
        migrate(database)
        runtime = Runtime(settings, database=database, cipher=VaultCipher(os.urandom(32), os.urandom(32)))
        runtime.authentication.provision('synthetic-native', 'Synthetic-Native-Fixture-83')
        http = TestClient(create_app(settings, runtime=runtime), base_url='http://localhost')
        class DependencyAdapter:
            def exchange(self, method, url, headers, body, cancel, timeout, limit):
                cancel.check()
                parts = urlsplit(url)
                response = http.request(method, parts.path + ('?' + parts.query if parts.query else ''), headers=headers, content=body)
                if len(response.content) > limit:
                    raise ValueError('Synthetic response limit.')
                return HTTPResult(response.status_code, response.content)
        core = CoreApplication(paths=RuntimePaths(base / 'desktop'), config=AppConfig(allow_cloud=True, speak_replies=False))
        core.cloud.client.transport = DependencyAdapter()
        studio = Studio(core)
        hud = HudService(studio)
        bridge = HudBridge(hud)
        window = webview.create_window('CLYDEX Phase 05 · synthetic native verification',
            str(ROOT / 'deployment/windows/artifacts/frontend/index.html'), js_api=bridge,
            width=1360, height=900, min_size=(340, 180), hidden=True, background_color='#060c14')
        hud.display.bind(window)
        def wait(expression, seconds=15):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                value = window.evaluate_js(expression)
                if value:
                    return value
                time.sleep(.08)
            raise AssertionError('UI condition not reached: ' + expression)
        def capture(name):
            from System import Action
            from System.IO import File, FileMode
            from Microsoft.Web.WebView2.Core import CoreWebView2CapturePreviewImageFormat
            stream = File.Open(str(output / (name + '.png')), FileMode.Create)
            tasks = []
            try:
                window.native.Invoke(Action(lambda: tasks.append(window.native.webview.CoreWebView2.CapturePreviewAsync(
                    CoreWebView2CapturePreviewImageFormat.Png, stream))))
                deadline = time.monotonic() + 8
                while not tasks[0].IsCompleted:
                    if time.monotonic() > deadline:
                        raise TimeoutError('Capture timeout.')
                    time.sleep(.03)
                tasks[0].GetAwaiter().GetResult()
            finally:
                stream.Dispose()
        def page(name):
            window.evaluate_js("[...document.querySelectorAll('nav button')].find(x=>x.title===" + json.dumps(name) + ').click()')
            time.sleep(.35)
        reviews = []
        def action(operation, values=None, *, configure=False):
            assert bridge.hud_command('cloud.configure' if configure else 'cloud.action',
                {'values': values} if configure else {'operation': operation, 'values': values or {}})['ok']
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                pending = core.engine.pending_review()
                if pending:
                    reviews.append(pending['digest'])
                    assert bridge.hud_command('approval.decide', {'id': pending['id'], 'approve': True})['ok']
                if not core.queue.busy and not studio._busy:
                    assert not core.cloud.error, core.cloud.error
                    return
                time.sleep(.03)
            raise TimeoutError('Reviewed action did not settle.')
        def verify():
            started = time.monotonic()
            try:
                assert window.events.loaded.wait(20)
                window.show()
                wait("!!document.querySelector('.overview-grid')")
                wait("!document.querySelector('.startup')")
                page('Personal Cloud')
                wait("document.body.innerText.includes('No service observation yet')")
                capture('cloud-unconfigured-1360')
                action('configure', {'endpoint': 'https://synthetic-cloud.invalid', 'enabled': True}, configure=True)
                action('login', {'login': 'synthetic-native', 'password': 'Synthetic-Native-Fixture-83'})
                action('collection.create', {'title': 'Synthetic engineering fixtures', 'description': 'No private documents'})
                action('reload')
                collection = core.cloud.results['reload']['collections']['items'][0]['id']
                source = base / 'synthetic-evidence.md'
                source.write_text('The synthetic CLYDEX verification marker is CYAN-05.\nThis is a deterministic test document.', encoding='utf-8')
                core.cloud.selection([source])
                selected = next(iter(core.cloud.selections))
                action('document.upload', {'selection': selected, 'collection_id': collection})
                assert runtime.worker.tick()
                action('reload')
                action('search', {'query': 'CYAN-05', 'mode': 'keyword', 'collection_id': collection})
                document = core.cloud.results['reload']['documents']['items'][0]
                action('cache.add', {'id': document['id'], 'hours': 24, 'quota_bytes': 10 * 1024 * 1024})
                page('Personal Cloud')
                wait("document.body.innerText.includes('simulated_test_repository')")
                capture('cloud-observed-1360')
                page('Knowledge Vault')
                wait("document.body.innerText.includes('CYAN-05')")
                wait("document.querySelector('.source-excerpt')?.closest('article')?.querySelector('h3')?.textContent==='synthetic-evidence.md'")
                capture('knowledge-1360')
                window.evaluate_js("[...document.querySelectorAll('h2')].find(x=>x.textContent==='Find grounded information').scrollIntoView({block:'start'})")
                time.sleep(.2)
                capture('knowledge-sources-1360')
                window.resize(760, 900)
                time.sleep(.5)
                capture('knowledge-760')
                result['responsive_overflow_760'] = window.evaluate_js('document.documentElement.scrollWidth>innerWidth+2')
                window.resize(1360, 900)
                from clydex.synchronization.contracts import CATEGORIES
                action('sync.configure', {'policy': {x: x in ('knowledge', 'memory', 'preferences', 'themes') for x in CATEGORIES}})
                action('sync.pull')
                page('Synchronization')
                wait("document.body.innerText.includes('INCREMENTAL CURSOR')")
                capture('synchronization-1360')
                action('device.pair', {'display_name': 'Synthetic Windows device', 'platform': 'Windows', 'scopes': ['vault.read']})
                pairing = core.cloud.results['device.pair']
                action('device.approve', {'id': pairing['id']})
                runtime.devices.claim(pairing['pairing_token'])
                # Clear the one-use token from presentation before screenshot.
                core.cloud.results.pop('device.pair', None)
                action('reload')
                page('Devices')
                wait("document.body.innerText.includes('Synthetic Windows device')")
                capture('devices-1360')
                cache_count = len(core.cloud.cache.snapshot(core.cloud.binding)['items'])
                assert cache_count == 1, 'Historical sync replay must preserve a newer cache revision.'
                result.update(passed=True, exact_reviews=len(reviews), document_status=document['status'],
                    citation_count=len(core.cloud.results['search']['items']), cache_count=len(core.cloud.cache.snapshot(core.cloud.binding)['items']),
                    elapsed_seconds=round(time.monotonic()-started, 3), native_picker='Not interactively exercised; explicit synthetic selection supplied',
                    bridge=window.evaluate_js('Object.keys(window.pywebview.api)'))
                result['python_working_set_bytes'] = hud.system.sample().get('process_memory_bytes')
            except Exception:
                import traceback
                result['failure'] = traceback.format_exc()
            finally:
                window.destroy()
        watchdog = threading.Timer(100, window.destroy)
        watchdog.start()
        try:
            webview.start(verify, gui='edgechromium', private_mode=True)
        finally:
            watchdog.cancel()
            core.close()
            result['shutdown_joined'] = core.wait_closed(15)
            runtime.close()
            http.close()
    (output / 'native-results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--desktop-site', type=Path)
    args = parser.parse_args()
    results = main(args.output.resolve(), args.desktop_site)
    print(json.dumps(results, indent=2))
    raise SystemExit(0 if results['passed'] and results['shutdown_joined'] else 1)
