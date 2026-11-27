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
    loader = importlib.machinery.SourceFileLoader('widget_smoke', str(ROOT / 'scripts/windows/clydex_widget.pyw'))
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
        window = webview.create_window('CLYDEX foundation smoke', str(ROOT / 'frontend/legacy/index.html'),
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
                window.evaluate_js("document.getElementById('intelligenceOpen').click()")
                deadline = time.monotonic() + 5
                while not window.evaluate_js("document.getElementById('intelligencePanel').open"):
                    assert time.monotonic() < deadline, 'Intelligence controls failed to open'
                    time.sleep(.05)
                assert window.evaluate_js("document.getElementById('providerId').options.length") == 7
                assert not core.memory.policy()['automatic']
                assert core.conversations.current.temporary
                window.evaluate_js("document.getElementById('conversationTitle').value='Synthetic smoke session';"
                                   "document.getElementById('historyPersistent').click()")
                deadline = time.monotonic() + 5
                review = None
                while time.monotonic() < deadline:
                    review = core.engine.pending_review()
                    if review:
                        break
                    time.sleep(.05)
                assert review and 'conversation.manage' in review['script']
                assert studio.decide(review['id'], True)
                deadline = time.monotonic() + 5
                while studio.snapshot()['busy']:
                    assert time.monotonic() < deadline, 'Conversation operation did not finish'
                    time.sleep(.05)
                assert not core.conversations.current.temporary
                assert core.conversations.current.title == 'Synthetic smoke session'
                assert b'Synthetic smoke session' not in core.store.path.read_bytes()
                assert all(not c.enabled for name, c in core.providers.configs.items() if name != 'codex')
                window.evaluate_js("document.getElementById('intelligencePanel').close();"
                                   "document.getElementById('voiceSettingsOpen').click()")
                deadline = time.monotonic() + 8
                while not window.evaluate_js("document.getElementById('voicePanel').open"):
                    assert time.monotonic() < deadline, 'Voice controls failed to open'
                    time.sleep(.05)
                assert window.evaluate_js("document.getElementById('personalityMode').options.length") == 9
                assert not core.voice.config.microphone_enabled
                assert core.voice.privacy.muted
                window.evaluate_js("document.getElementById('v_volume').value=37;"
                                   "document.getElementById('voiceSave').click()")
                deadline = time.monotonic() + 8
                while not core.engine.pending_review():
                    assert time.monotonic() < deadline, 'Voice configuration review did not open'
                    time.sleep(.05)
                review = core.engine.pending_review()
                assert 'voice.configure' in review['script']
                assert studio.decide(review['id'], True)
                while studio.snapshot()['busy']:
                    assert time.monotonic() < deadline, 'Voice configuration did not finish'
                    time.sleep(.05)
                assert core.voice.config.volume == 37
                assert not core.voice.config.microphone_enabled
                assert not core.voice.snapshot()['background_armed']
                assert not studio.microphone()
                core.voice.privacy.probe = lambda: True  # Synthetic lock, never lock the owner's PC.
                deadline = time.monotonic() + 5
                while window.evaluate_js("document.getElementById('privacyShield').hidden"):
                    assert time.monotonic() < deadline, 'Lock privacy shield did not appear'
                    time.sleep(.05)
                result.update(webview='passed', checks='WebView2 startup, local assets, bridge, Stop, review UI, '
                              'seven providers, encrypted session creation, nine personality profiles, reviewed '
                              'voice settings, disabled/muted defaults, synthetic lock privacy shield')
            except Exception as exc:
                result['error_type'] = type(exc).__name__
            finally:
                window.destroy()
        timer = threading.Timer(45, window.destroy)
        timer.daemon = True
        timer.start()
        try:
            with patch.object(window, 'show'):
                webview.start(verify, gui='edgechromium', private_mode=True)
        finally:
            timer.cancel()
            core.close()
            assert core.wait_closed(5), 'Core native resources did not close'
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
