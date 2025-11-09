# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ['../src/main.py'],
    pathex=['../src'],
    hiddenimports=['qframelesswindow'],
    optimize=1
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    name='Wonky Window',
    version='../version_info.txt',
    icon='../src/logos/icons.ico',
    console=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name=f"WonkyWindow-portable-v{os.getenv('PYI_APP_VERSION', '1.0.0')}",
)