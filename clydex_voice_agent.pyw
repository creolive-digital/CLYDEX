"""Compatibility launcher for the CLYDEX Studio desktop window."""
from pathlib import Path
import sys

_source = Path(__file__).resolve().parent / 'src'
if _source.is_dir() and str(_source) not in sys.path:
    sys.path.insert(0, str(_source))

from clydex.desktop.studio import Studio


if __name__ == '__main__':
    import webview
    studio = Studio()
    page = Path(__file__).resolve().parent / 'studio_ui' / 'index.html'
    window = webview.create_window('CLYDEX Voice Agent', str(page), js_api=studio,
                                   width=1220, height=780, min_size=(760, 510),
                                   background_color='#0E1416')
    window.events.closed += studio._close
    webview.start(gui='edgechromium')
