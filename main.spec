# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the XHider Deobfuscator CLI (main.py).
# Build with:  .venv\Scripts\pyinstaller.exe main.spec
# Output:      dist\decbot.exe (onefile, console)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Lua hook scripts loaded at runtime via SCRIPT_DIR
        ('universal/*.lua', 'universal'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # heavy packages present in .venv but unused by main.py
        'numpy', 'imageio', 'tkinter',
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='decbot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
