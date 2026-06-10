# -*- mode: python ; coding: utf-8 -*-
# Onedir-Build OHNE UPX.
# Wichtig: KEIN onefile + KEIN UPX. Eine onefile-EXE entpackt sich bei jedem
# Start nach %TEMP% und laedt von dort DLLs - das fuehrt (besonders vom
# Netzlaufwerk und mit Virenscanner) zu 0xc0000142 (DLL-Init-Fehler) und kann
# Windows hart einfrieren. UPX zerstoert ausserdem haeufig Qt5/OpenCV-DLLs.
# Den fertigen "dist\DoorBird_Stream_Viewer"-Ordner immer LOKAL ausfuehren,
# nicht direkt vom NFS-Share starten.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('Spy.png', '.')],
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
    name='DoorBird_Stream_Viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Spy.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DoorBird_Stream_Viewer',
)
