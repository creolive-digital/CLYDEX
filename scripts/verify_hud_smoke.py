"""Native Windows HUD verification with an isolated profile and no audio/provider calls.

Build frontend first. Screenshots capture only this WebView's rendered client area.
No desktop screenshot, microphone, speaker, weather or provider probe is used.
"""
import argparse
import faulthandler
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main(output: Path) -> dict:
    import webview
    from clydex.core.application import CoreApplication
    from clydex.core.config import AppConfig, RuntimePaths
    from clydex.desktop.hud import HudBridge, HudService
    from clydex.desktop.studio import Studio
    output.mkdir(parents=True, exist_ok=True)
    result = {'kind': 'native Windows WebView2; isolated synthetic profile', 'passed': False}
    with tempfile.TemporaryDirectory(prefix='clydex-hud-smoke-') as folder:
        core = CoreApplication(paths=RuntimePaths(Path(folder)), config=AppConfig(allow_cloud=False, speak_replies=False))
        studio = Studio(core)
        hud = HudService(studio)
        bridge = HudBridge(hud)
        window = webview.create_window('CLYDEX · Phase 04 verification (isolated profile)',
            str(ROOT / 'deployment/windows/artifacts/frontend/index.html'), js_api=bridge,
            width=1360, height=900, min_size=(340, 180), hidden=True, background_color='#060c14')
        hud.display.bind(window)

        def wait(expression, seconds=12):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                value = window.evaluate_js(expression)
                if value:
                    return value
                time.sleep(.08)
            raise AssertionError(f'UI condition not reached: {expression}')

        def click(label):
            encoded = json.dumps(label)
            assert window.evaluate_js(f"(()=>{{const b=[...document.querySelectorAll('nav button')].find(b=>b.title==={encoded});if(b)b.click();return !!b;}})()"), label

        def capture(name):
            from System import Action
            from System.IO import File, FileMode
            from Microsoft.Web.WebView2.Core import CoreWebView2CapturePreviewImageFormat
            stream = File.Open(str(output / f'{name}.png'), FileMode.Create)
            tasks = []
            try:
                window.native.Invoke(Action(lambda: tasks.append(window.native.webview.CoreWebView2.CapturePreviewAsync(
                    CoreWebView2CapturePreviewImageFormat.Png, stream))))
                deadline = time.monotonic() + 8
                while not tasks[0].IsCompleted:
                    if time.monotonic() > deadline:
                        raise TimeoutError('Native screenshot task did not complete')
                    time.sleep(.03)
                tasks[0].GetAwaiter().GetResult()
            finally:
                stream.Dispose()

        def review(approve=True):
            wait("!!document.querySelector('dialog[open]')")
            pending = core.engine.pending_review()
            assert pending and pending['id']
            assert bridge.hud_command('approval.decide', {'id': pending['id'], 'approve': approve})['ok']
            wait("!document.querySelector('dialog[open]')")
            deadline = time.monotonic() + 10
            while core.queue.busy or studio._busy:
                assert time.monotonic() < deadline
                time.sleep(.05)

        def verify():
            try:
                assert window.events.loaded.wait(20), 'WebView load timeout'
                window.show()
                wait("!!document.querySelector('.overview-grid')")
                wait("document.fonts.status==='loaded'")
                if window.evaluate_js("!!document.querySelector('.startup')"):
                    capture('startup')
                wait("!document.querySelector('.startup')")
                result['bridge'] = window.evaluate_js("Object.keys(window.pywebview.api)")
                assert set(result['bridge']) == {'hud_snapshot', 'hud_read', 'hud_command'}
                assert core.voice.privacy.muted and not core.voice.config.microphone_enabled
                time.sleep(1)
                capture('overview-1360')
                result['webgl'] = bool(window.evaluate_js("document.querySelector('.avatar-field canvas')"))
                result['viewport'] = window.evaluate_js("({width:innerWidth,height:innerHeight,dpr:devicePixelRatio})")
                before = int(window.evaluate_js("document.querySelector('[data-render-frames]')?.dataset.renderFrames||0"))
                time.sleep(2)
                after = int(window.evaluate_js("document.querySelector('[data-render-frames]')?.dataset.renderFrames||0"))
                result['rendered_frames_over_2s'] = after - before
                result['system_counters'] = hud.system.sample()
                window.minimize()
                time.sleep(.5)
                before = int(window.evaluate_js("document.querySelector('[data-render-frames]')?.dataset.renderFrames||0"))
                time.sleep(1)
                after = int(window.evaluate_js("document.querySelector('[data-render-frames]')?.dataset.renderFrames||0"))
                assert after == before, (before, after)
                result['minimized_frames_over_1s'] = after - before
                window.restore()
                hud.display.set_visible(True)
                window.resize(760, 720)
                time.sleep(.4)
                assert window.evaluate_js('document.documentElement.scrollWidth<=innerWidth'), 'Horizontal viewport overflow'
                capture('overview-760')
                window.resize(1360, 900)
                for label, marker in [('Intelligence','Your intelligence network'), ('Memory','What CLYDEX remembers'),
                                      ('Voice','A clear channel'), ('Personality','Personality'), ('Settings','Settings'),
                                      ('Notifications','Notifications'), ('Conversation','Conversation')]:
                    click(label)
                    wait(f"document.body.innerText.includes({json.dumps(marker)})")
                    if label == 'Voice':
                        wait("document.body.innerText.includes('Recognition language')")
                    if label == 'Intelligence':
                        wait("document.querySelectorAll('.provider-card').length===7")
                    if label in ('Intelligence', 'Memory', 'Voice', 'Settings'):
                        time.sleep(.4)
                        capture(label.lower())
                    if label == 'Intelligence':
                        assert window.evaluate_js("document.querySelectorAll('.provider-card').length") == 7
                click('Memory')
                assert bridge.hud_command('memory.manage', {'values': {'operation': 'add', 'category': 'preferences',
                    'value': 'Synthetic Phase 04 local-only preference', 'local_only': True}})['ok']
                review()
                wait("document.body.innerText.includes('Synthetic Phase 04 local-only preference')")
                record = core.memory.repository.list()[0]
                assert record['local_only'] and not core.memory.policy()['automatic']
                assert b'Synthetic Phase 04 local-only preference' not in core.store.path.read_bytes()
                assert bridge.hud_command('memory.manage', {'values': {'operation': 'delete', 'id': record['id']}})['ok']
                review()
                wait("!document.body.innerText.includes('Synthetic Phase 04 local-only preference')")
                result['memory_crud_encryption_and_ui_refresh'] = True
                click('Overview')
                assert bridge.hud_command('preferences.configure', {'values': {'theme': 'midnight', 'reduced_motion': True}})['ok']
                wait("!!document.querySelector('dialog[open] .exact-action')")
                assert window.evaluate_js("document.activeElement.textContent.includes('Cancel action')"), 'Cancel must receive native modal focus'
                capture('approval')
                review()
                assert hud.preferences.values.reduced_motion
                wait("document.documentElement.dataset.motion==='off'")
                time.sleep(.3)  # Allow the final static redraw/React effect, not continuous animation.
                before = int(window.evaluate_js("document.querySelector('[data-render-frames]')?.dataset.renderFrames||0"))
                time.sleep(1)
                assert int(window.evaluate_js("document.querySelector('[data-render-frames]')?.dataset.renderFrames||0")) == before
                result['reduced_motion_frames_over_1s'] = 0
                assert bridge.hud_command('display.mode', {'mode': 'widget'})['ok']
                wait("!!document.querySelector('.display-widget')")
                wait("!!document.querySelector('.widget-panel')")
                assert bridge.hud_command('widget.action', {'operation': 'timer.set', 'seconds': 30})['ok']
                deadline = time.monotonic() + 10
                while core.queue.busy or studio._busy:
                    assert time.monotonic() < deadline
                    time.sleep(.05)
                assert hud.widget.snapshot()['status'] == 'ready', hud.widget.snapshot()
                assert bridge.hud_command('widget.action', {'operation': 'timer.toggle'})['ok']
                deadline = time.monotonic() + 5
                while not hud.widget.snapshot().get('timer_running'):
                    assert time.monotonic() < deadline
                    time.sleep(.05)
                worker = hud.widget._thread
                window.evaluate_js("[...document.querySelectorAll('.widget-panel [role=tab]')].find(b=>b.textContent.trim()==='timer').click()")
                wait("!!document.querySelector('.time-tool')")
                wait("document.body.innerText.includes('Counting down')")
                assert window.evaluate_js("(()=>{const r=document.querySelector('.stop-button').getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;})()"), 'Widget Stop must stay visible'
                capture('smart-widget')
                for mode in ('floating', 'mini', 'fullscreen', 'window'):
                    assert bridge.hud_command('display.mode', {'mode': mode})['ok']
                    wait(f"!!document.querySelector('.display-{mode}')")
                    time.sleep(.25)
                    if mode in ('floating', 'mini'):
                        capture(mode)
                    assert hud.widget._thread is worker
                assert 0 < hud.widget.snapshot()['timer_remaining'] < 30
                result['shared_timer_survives_modes'] = True
                monitors = hud.display.monitors()
                for index, area in enumerate(monitors):
                    assert bridge.hud_command('display.monitor', {'index': index})['ok']
                    assert area['x'] <= window.x < area['x'] + area['width']
                result['native_monitor_moves'] = len(monitors)
                result['native_modes'] = ['window', 'fullscreen', 'widget', 'floating', 'mini']
                print('HUD smoke: five native modes verified', flush=True)
                # Native tray startup is explicitly reviewed, in this disposable profile only.
                assert bridge.hud_command('voice.configure', {'values': {'tray_enabled': True}})['ok']
                review()
                assert studio._activations.tray_available
                print('HUD smoke: reviewed native tray started', flush=True)
                assert bridge.hud_command('display.mode', {'mode': 'tray'})['ok']
                assert not hud.display.visible and core.voice.privacy.muted
                assert bridge.hud_command('preferences.configure', {'values': {'sound_volume': 20}})['ok']
                print('HUD smoke: review requested from tray', flush=True)
                review(False)
                print('HUD smoke: tray review canceled', flush=True)
                assert hud.display.mode == 'window' and hud.display.visible
                result['native_modes'].append('tray')
                result['approval_restores_hidden_window'] = True
                core.voice.privacy.probe = lambda: True
                wait("!!document.querySelector('.privacy-shield')")
                assert not window.evaluate_js("document.querySelector('nav, textarea, dialog, .message')")
                capture('locked-synthetic-probe')
                assert bridge.hud_command('voice.stop', {})['ok']
                assert bridge.hud_command('voice.mute', {'muted': True})['ok']
                core.voice.privacy.probe = lambda: False
                wait("!!document.querySelector('.overview-grid')")
                # Lose WebGL deliberately; the exact owner reference and controls must survive.
                window.evaluate_js("(()=>{const c=document.querySelector('canvas');if(c)c.dispatchEvent(new Event('webglcontextlost',{cancelable:true}));})()")
                wait("document.body.innerText.includes('WebGL unavailable')")
                capture('webgl-fallback')
                result.update(passed=True, no_audio_or_network=True, microphone_muted=core.voice.privacy.muted,
                    limits='No real lock, acoustic/model/provider tests, human accessibility review or mixed-DPI hardware qualification')
            except Exception:
                result['failure'] = traceback.format_exc()
                result['dom_text'] = window.evaluate_js('document.body.innerText')
                result['snapshot'] = bridge.hud_snapshot()
                result['page_diagnostics'] = window.evaluate_js("({href:location.href,html:document.body.innerHTML,resources:performance.getEntriesByType('resource').map(x=>({name:x.name,duration:x.duration}))})")
                window.evaluate_js("window._hudImport='pending';import(document.querySelector('script[type=module]').src).then(()=>window._hudImport='imported').catch(e=>window._hudImport=e.toString())")
                time.sleep(.5)
                result['import_diagnostics'] = window.evaluate_js('window._hudImport')
                (output / 'failure-details.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
            finally:
                # Clear the synthetic probe before shutdown; native shutdown ownership still applies.
                core.voice.privacy.probe = lambda: False
                window.destroy()

        watchdog = threading.Timer(120, window.destroy)
        watchdog.daemon = True
        watchdog.start()
        try:
            faulthandler.dump_traceback_later(45)
            webview.start(verify, gui='edgechromium', private_mode=True)
        finally:
            faulthandler.cancel_dump_traceback_later()
            watchdog.cancel()
            core.close()
            result['shutdown_joined'] = core.wait_closed(10)
    (output / 'native-results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = main(args.output.resolve())
    print(json.dumps(results, indent=2))
    raise SystemExit(0 if results['passed'] and results['shutdown_joined'] else 1)
