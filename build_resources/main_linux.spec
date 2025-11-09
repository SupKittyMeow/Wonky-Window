# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    hiddenimports=['qframelesswindow'],
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='Wonky Window',
    console=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='Wonky Window',
)
