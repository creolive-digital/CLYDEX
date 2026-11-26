# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the CLYDEX voice agent (pywebview / Edge WebView2)."""
from PyInstaller.utils.hooks import collect_all

datas = [
    ('studio_ui', 'studio_ui'),
    ('assets/legacy/clydex_hologram.png', '.'),
    ('assets/legacy/clydex_projection.png', '.'),
]
binaries = []
hiddenimports = ['clydex_engine', 'clydex_spectrum', 'win32timezone']

# The package lives under src; collect migration SQL and Windows helper scripts.
from PyInstaller.utils.hooks import collect_data_files
datas += collect_data_files('clydex')

# Collect all sub-packages, data files, and native DLLs for packages that
# ship compiled extensions or use runtime data discovery.
for _pkg in ['webview', 'faster_whisper', 'ctranslate2', 'av', 'sounddevice', 'numpy']:
    _d, _b, _h = collect_all(_pkg)
    datas    += _d
    binaries += _b
    hiddenimports += _h

a = Analysis(
    ['clydex_voice_agent.pyw'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', '_tkinter'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='clydex_voice_agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,   # keep off — ctranslate2 / av DLLs break with UPX
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='clydex_voice_agent',
)
