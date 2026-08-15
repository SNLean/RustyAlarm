# -*- mode: python ; coding: utf-8 -*-
# Panel web de configuracion. Build: pyinstaller webapp.spec
# Salida: dist/rust-panel/rust-panel.exe
#
# config.json NO se empaqueta a proposito: se crea y se edita junto al exe.


a = Analysis(
    ['webapp.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('web/index.html', 'web'),
        ('alarma.wav', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='rust-panel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='rust-panel',
)
