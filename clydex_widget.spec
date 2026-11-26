# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the CLYDEX desktop clock / weather widget."""

a = Analysis(
    ['clydex_widget.pyw'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('studio_ui', 'studio_ui'),
        ('clydex_hologram.png', '.'),
        ('clydex_projection.png', '.'),
    ],
    hiddenimports=['clydex_theme'],
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
