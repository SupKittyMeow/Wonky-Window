# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtMultimedia', 'PySide6.QtQuick', 'PySide6.QtPrintSupport'],
    pathex=['src'],
    hiddenimports=['qframelesswindow'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
    optimize=1
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='Wonky Window',
    version='version_info.txt',
    icon='src/logos/icons.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)
