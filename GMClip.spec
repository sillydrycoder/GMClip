# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['block_editor\\__main__.py'],
    pathex=[],
    binaries=[('ffmpeg/windows\\ffmpeg.exe', '.'), ('ffmpeg/windows\\ffplay.exe', '.'), ('ffmpeg/windows\\ffprobe.exe', '.')],
    datas=[('label_manager.py', '.')],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets', 'cv2', 'numpy', 'pydub'],
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
    a.binaries,
    a.datas,
    [],
    name='GMClip',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
