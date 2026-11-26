"""Compatibility import for the V2 desktop package."""
from pathlib import Path
import sys

_source = Path(__file__).resolve().parent / 'src'
if _source.is_dir() and str(_source) not in sys.path:
    sys.path.insert(0, str(_source))

from clydex.desktop.widget import *  # noqa: F401,F403,E402


if __name__ == '__main__':
    ClydexWidget().run()
