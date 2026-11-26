# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the CLYDEX desktop clock / weather widget."""

from pathlib import Path

ROOT = Path(SPECPATH).resolve().parents[1]

a = Analysis(
    [str(ROOT / 'scripts/windows/clydex_widget.pyw')],
    pathex=[str(ROOT / 'src')],
    binaries=[],
    datas=[
        (str(ROOT / 'frontend/legacy'), 'frontend/legacy'),
        (str(ROOT / 'assets/legacy/clydex_hologram.png'), '.'),
        (str(ROOT / 'assets/legacy/clydex_projection.png'), '.'),
    ],
    hiddenimports=['clydex.desktop.theme'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='clydex_widget',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='clydex_widget',
)
