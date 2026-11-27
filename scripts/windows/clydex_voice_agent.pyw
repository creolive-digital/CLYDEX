"""Compatibility launcher for the CLYDEX Studio desktop window."""
from pathlib import Path
from dataclasses import replace
import os
import sys

ROOT = (Path(sys._MEIPASS) if getattr(sys, 'frozen', False)
        else Path(__file__).resolve().parents[2])
_source = ROOT / 'src'
if _source.is_dir() and str(_source) not in sys.path:
    sys.path.insert(0, str(_source))

from clydex.desktop.studio import Studio


if __name__ == '__main__':
    import webview
    studio = Studio()
    hud_page = (ROOT / 'frontend/hud/index.html' if getattr(sys, 'frozen', False)
                else ROOT / 'deployment/windows/artifacts/frontend/index.html')
    legacy = '--legacy' in sys.argv or os.environ.get('CLYDEX_FRONTEND') == 'legacy' or not hud_page.is_file()
    if legacy:
        page, bridge = ROOT / 'frontend/legacy/index.html', studio
    else:
        from clydex.desktop.hud import HudService, HudBridge
        hud = HudService(studio)
        if '--silent' in sys.argv:
            hud.preferences.values = replace(hud.preferences.values, sounds_muted=True, startup_greeting=False, startup_sound=False)
        if '--reduced-motion' in sys.argv:
            hud.preferences.values = replace(hud.preferences.values, reduced_motion=True)
        page, bridge = hud_page, HudBridge(hud)
    window = webview.create_window('CLYDEX · Your Personal Digital Intelligence', str(page), js_api=bridge,
                                   width=1360 if not legacy else 1220, height=900 if not legacy else 780,
                                   min_size=(340, 180) if not legacy else (760, 510), background_color='#060c14')
    if legacy:
        window.events.closed += studio._close
        window.events.minimized += lambda: studio.set_voice_visible(False)
        window.events.shown += lambda: studio.set_voice_visible(True)
        window.events.restored += lambda: studio.set_voice_visible(True)
    else:
        hud.display.bind(window)
    webview.start(gui='edgechromium')
