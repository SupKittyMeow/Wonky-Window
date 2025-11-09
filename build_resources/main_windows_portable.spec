# -*- mode: python ; coding: utf-8 -*-


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
    console=False,
    onefile=True
)
