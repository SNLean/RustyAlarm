# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['rust.py'],
    pathex=[],
    binaries=[],
    # config.json NO se empaqueta: tiene que ser editable y vivir junto al exe.
    # alarma.wav va como fallback; si el usuario deja su propio alarma.wav al
    # lado del exe, core.sound_path() prefiere ese.
    datas=[('alarma.wav', '.')],
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
    name='rust',
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
    name='rust',
)
