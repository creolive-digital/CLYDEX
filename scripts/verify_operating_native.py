"""Actual WebView2/Core/DPAPI with synthetic workflows; no network/audio/capture.

Screenshots capture only this test window client area. The script approves only
the explicitly constructed synthetic fixture operations below, never real work.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main(output):
    import webview
    from clydex.core.application import CoreApplication
    from clydex.core.config import AppConfig, RuntimePaths
    from clydex.desktop.hud import HudBridge, HudService
    from clydex.desktop.studio import Studio
    from clydex.automation.routines import template
    output.mkdir(parents=True, exist_ok=True)
    result = dict(kind='Actual Windows WebView2, Core and DPAPI; synthetic local workflows', passed=False,
                  no_external_network=True, no_audio_models_or_desktop_capture=True)
    with tempfile.TemporaryDirectory(prefix='clydex-operating-native-') as folder:
        core = CoreApplication(paths=RuntimePaths(Path(folder)), config=AppConfig(allow_cloud=False, speak_replies=False))
        studio = Studio(core)
        hud = HudService(studio)
        bridge = HudBridge(hud)
        window = webview.create_window('CLYDEX Phase 06 · synthetic native verification',
            str(ROOT / 'deployment/windows/artifacts/frontend/index.html'), js_api=bridge,
            width=1360, height=900, min_size=(340, 180), hidden=True, background_color='#060c14')
        hud.display.bind(window)
        reviews = []
        def wait(expression, seconds=15):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                value = window.evaluate_js(expression)
                if value:
                    return value
                time.sleep(.08)
            raise AssertionError('UI condition not reached: ' + expression)
        def page(name):
            assert window.evaluate_js("(()=>{const b=[...document.querySelectorAll('nav button')].find(x=>x.title===" +
                json.dumps(name) + ");if(b)b.click();return !!b;})()")
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
                        raise TimeoutError('Client screenshot did not complete.')
                    time.sleep(.03)
                tasks[0].GetAwaiter().GetResult()
            finally:
                stream.Dispose()
        def action(operation, values, *, stop=False):
            assert bridge.hud_command('operating.action', {'operation': operation, 'values': values})['ok']
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                pending = core.engine.pending_review()
                if pending:
                    reviews.append(pending['digest'])
                    assert bridge.hud_command('approval.decide', {'id': pending['id'], 'approve': True})['ok']
                if stop and core.operating.repository.history() and core.operating.repository.history()[0]['status'] == 'running':
                    bridge.hud_command('voice.stop', {})
                if not core.queue.busy and not studio._busy:
                    if not stop:
                        assert not core.operating.error
                    return
                time.sleep(.02)
            raise TimeoutError('Synthetic native operation did not finish.')
        def verify():
            started = time.monotonic()
            try:
                assert window.events.loaded.wait(20)
                window.show()
                wait("!!document.querySelector('.overview-grid')")
                wait("!document.querySelector('.startup')")
                page('Automation Studio')
                wait("!!document.querySelector('.workflow-canvas')")
                # Real DOM gestures exercise palette, connection controls and Python preview.
                window.evaluate_js("[...document.querySelectorAll('button')].find(b=>b.textContent==='Add node').click()")
                wait("document.querySelectorAll('.workflow-node').length===2")
                window.evaluate_js("(()=>{for(const [name,value] of [['Connection from','start'],['Connection to','node_2']]){const s=document.querySelector('select[aria-label=\"'+name+'\"]');s.value=value;s.dispatchEvent(new Event('change',{bubbles:true}));}})()")
                window.evaluate_js("[...document.querySelectorAll('button')].find(b=>b.textContent==='Connect nodes').click()")
                wait("document.querySelectorAll('.workflow-edge').length===1")
                window.evaluate_js("[...document.querySelectorAll('button')].find(b=>b.textContent==='Validate and preview').click()")
                wait("document.body.innerText.includes('workflow.preview')")
                capture('automation-editor-1360')
                definition = template('custom')
                definition['name'] = 'Synthetic local health routine'
                definition['nodes'] = [dict(id='sample', kind='tool', config={'tool': 'monitoring.sample', 'arguments': {}}, x=60, y=80),
                    dict(id='receipt', kind='output', config={'value': {'$ref': 'sample.os'}}, x=390, y=80)]
                definition['edges'] = [{'from': 'sample', 'to': 'receipt', 'port': 'next'}]
                action('workflow.save', {'definition': definition, 'revision': 0})
                action('workflow.enable', {'id': definition['id'], 'revision': 1, 'enabled': True})
                action('workflow.run', {'id': definition['id'], 'inputs': {}})
                assert core.operating.repository.history()[0]['status'] == 'complete'
                wait("document.body.innerText.includes('Synthetic local health routine')")
                window.evaluate_js("[...document.querySelectorAll('.operating-record')].find(b=>b.innerText.includes('Synthetic local health routine')).click()")
                wait("document.body.innerText.includes('receipt')")
                capture('automation-history-1360')
                page('Developer Center')
                wait("document.body.innerText.includes('Selected content assistance')")
                capture('developer-1360')
                page('Plugins')
                wait("document.body.innerText.includes('No installed plugins')")
                capture('plugins-1360')
                page('Integrations')
                wait("document.body.innerText.includes('MCP server')")
                capture('integrations-1360')
                page('Monitoring')
                wait("document.body.innerText.includes('system-wide utilization')")
                capture('monitoring-1360')
                result['observed_metrics'] = core.operating.system.sample()
                page('Automation Studio')
                wait("document.body.innerText.includes('Synthetic local health routine')")
                window.evaluate_js("[...document.querySelectorAll('.operating-record')].find(b=>b.innerText.includes('Synthetic local health routine')).click()")
                window.resize(760, 900)
                time.sleep(.4)
                wait("!!document.querySelector('.workflow-canvas')")
                result['responsive_overflow_760'] = window.evaluate_js('document.documentElement.scrollWidth>innerWidth+2')
                capture('automation-editor-760')
                delayed = template('custom')
                delayed['name'] = 'Synthetic cancellation fixture'
                delayed['nodes'] = [dict(id='pause', kind='delay', config={'seconds': 10}, x=60, y=80),
                    dict(id='never', kind='tool', config={'tool': 'monitoring.sample', 'arguments': {}}, x=390, y=80)]
                delayed['edges'] = [{'from': 'pause', 'to': 'never', 'port': 'next'}]
                action('workflow.save', {'definition': delayed, 'revision': 0})
                action('workflow.enable', {'id': delayed['id'], 'revision': 1, 'enabled': True})
                action('workflow.run', {'id': delayed['id'], 'inputs': {}}, stop=True)
                latest = core.operating.repository.history()[0]
                assert latest['status'] == 'cancelled' and 'never' not in latest['nodes']
                result.update(passed=True, exact_reviews=len(reviews), completed_run=True, stop_prevented_next_action=True,
                    elapsed_seconds=round(time.monotonic() - started, 3),
                    bridge=window.evaluate_js('Object.keys(window.pywebview.api)'),
                    native_picker='Not interactively exercised; no private paths selected',
                    limits='No live services, SQL Server, camera/screen capture, acoustic or physical-lock acceptance')
            except Exception:
                result['failure'] = traceback.format_exc()
                result['dom_text'] = window.evaluate_js('document.body.innerText')
            finally:
                window.destroy()
        watchdog = threading.Timer(100, window.destroy)
        watchdog.daemon = True
        watchdog.start()
        try:
            webview.start(verify, gui='edgechromium', private_mode=True)
        finally:
            watchdog.cancel()
            core.close()
            result['shutdown_joined'] = core.wait_closed(15)
    (output / 'native-results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = main(args.output.resolve())
    print(json.dumps(value, indent=2))
    raise SystemExit(0 if value['passed'] and value['shutdown_joined'] else 1)
