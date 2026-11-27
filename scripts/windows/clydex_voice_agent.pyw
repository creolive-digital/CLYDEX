"""Compatibility launcher for the CLYDEX Studio desktop window."""
from pathlib import Path
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
    page = ROOT / 'frontend' / 'legacy' / 'index.html'
    window = webview.create_window('CLYDEX Voice Agent', str(page), js_api=studio,
                                   width=1220, height=780, min_size=(760, 510),
                                   background_color='#0E1416')
    window.events.closed += studio._close
    window.events.minimized += lambda: studio.set_voice_visible(False)
    window.events.shown += lambda: studio.set_voice_visible(True)
    window.events.restored += lambda: studio.set_voice_visible(True)
    webview.start(gui='edgechromium')
