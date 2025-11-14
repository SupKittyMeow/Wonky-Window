# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['../src/main.py'],
    pathex=['../src'],
    hiddenimports=['qframelesswindow'],
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='Wonky Window',
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='Wonky Window',
)

app = BUNDLE(
    coll,
    name='Wonky Window.app',
    icon='../src/logos/icons.icns',
    bundle_identifier='com.supkittymeow.wonkywindow',
    info_plist={
        'CFBundleDisplayName': 'Wonky Window',
        'CFBundleName': 'Wonky Window',
        'CFBundleShortVersionString': '1',
        'CFBundleVersion': '1.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSUIElement': True
    },
)
