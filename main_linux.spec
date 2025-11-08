# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtMultimedia', 'PySide6.QtQuick', 'PySide6.QtPrintSupport'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=['qframelesswindow'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Wonky Window',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    name='Wonky Window',
)
