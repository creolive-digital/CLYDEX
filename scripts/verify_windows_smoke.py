"""Safe UI startup checks. No microphone, mailbox, model call or weather request.

Run from the checkout: python scripts/verify_windows_smoke.py [--webview] [--credentials]
The optional WebView window is hidden and closes itself. This is automated smoke
evidence, not human visual/accessibility or real integration acceptance.
"""
import argparse
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import uuid
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))


def widget_smoke() -> dict:
    loader = importlib.machinery.SourceFileLoader('widget_smoke', str(ROOT / 'clydex_widget.pyw'))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    with patch.object(module.ClydexWidget, 'request_weather'):
        widget = module.ClydexWidget()
    try:
        widget.root.withdraw()
        widget.root.bell = lambda: None
        widget.root.update()
        widget.set_duration(30)
        widget.toggle_timer()
        assert widget.timer_end is not None
        widget.toggle_timer()
        assert widget.timer_end is None and widget.timer_remaining > 0
        widget.toggle_timer()
        widget.timer_end = time.monotonic() - 1
        widget.update_tools(time.monotonic(), module.datetime.now())
        assert widget.alerts[0][0] == 'Timer'
        widget.dismiss_alert()
        widget.show_page('Alarm')
        widget.toggle_alarm()
        assert widget.alarm_at is not None
        widget.toggle_alarm()
        assert widget.alarm_at is None
        widget.show_page('Stopwatch')
        widget.toggle_stopwatch()
        widget.mark_lap()
        assert widget.lap_count == 1
        widget.toggle_stopwatch()
        widget.reset_stopwatch()
        widget.show_page('Clock')
        widget.toggle_size()
        widget.root.update()
        return {'widget': 'passed', 'checks': 'Tk startup, clock, compact/full, timer, alarm, stopwatch',
                'weather': 'mocked; no network request'}
    finally:
        widget.root.destroy()


def webview_smoke() -> dict:
    import webview
    from clydex.core.application import CoreApplication
    from clydex.core.config import AppConfig, RuntimePaths
    from clydex.desktop.studio import Studio
    result = {'webview': 'failed'}
    with tempfile.TemporaryDirectory(prefix='clydex-ui-smoke-') as folder:
        core = CoreApplication(paths=RuntimePaths(Path(folder)),
                               config=AppConfig(allow_cloud=False, speak_replies=False))
        studio = Studio(core)
        window = webview.create_window('CLYDEX foundation smoke', str(ROOT / 'studio_ui/index.html'),
                                       js_api=studio, hidden=True, width=1220, height=780)
        def verify():
            try:
                if not window.events.loaded.wait(15):
                    return
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    ready = window.evaluate_js(
                        "Boolean(window.pywebview?.api?.stop && document.getElementById('stopTaskBtn'))")
                    if ready:
                        break
                    time.sleep(.05)
                assert ready, 'WebView bridge or Stop control unavailable'
                assert window.evaluate_js("document.querySelector('#taskReview details').open")
                assert studio.snapshot()['state'] == 'READY'
                result.update(webview='passed', checks='WebView2 startup, local assets, bridge, Stop, review UI')
            except Exception as exc:
                result['error_type'] = type(exc).__name__
            finally:
                window.destroy()
        timer = threading.Timer(25, window.destroy)
        timer.daemon = True
        timer.start()
        try:
            webview.start(verify, gui='edgechromium', private_mode=True)
        finally:
            timer.cancel()
            core.close()
    if result['webview'] != 'passed':
        raise RuntimeError(json.dumps(result))
    return result


def credential_smoke() -> dict:
    from clydex.security.credentials import CredentialStore
    store = CredentialStore()
    name = 'verification.' + uuid.uuid4().hex
    try:
        store.set(name, 'synthetic-foundation-check')
        assert store.get(name) == 'synthetic-foundation-check'
    finally:
        store.delete(name)
    assert store.get(name) is None
    return {'credentials': 'passed', 'checks': 'native write/read/delete of a synthetic test value'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--webview', action='store_true')
    parser.add_argument('--credentials', action='store_true')
    args = parser.parse_args()
    print(json.dumps(widget_smoke()))
    if args.webview:
        print(json.dumps(webview_smoke()))
    if args.credentials:
        print(json.dumps(credential_smoke()))
