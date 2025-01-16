import os
import sys
import shutil
from pathlib import Path
import PyInstaller.__main__

def get_platform_info():
    if sys.platform == 'win32':
        return {
            'ffmpeg_path': 'ffmpeg/windows',
            'ffmpeg_files': ['ffmpeg.exe', 'ffplay.exe', 'ffprobe.exe'],
            'separator': ';',
            'output_name': 'GMClip.exe'
        }
    elif sys.platform == 'darwin':
        return {
            'ffmpeg_path': 'ffmpeg/mac',
            'ffmpeg_files': ['ffmpeg' , 'ffplay', 'ffprobe'],
            'separator': ':',
            'output_name': 'GMClip'
        }
    else:  # Linux
        return {
            'ffmpeg_path': 'ffmpeg/linux',
            'ffmpeg_files': ['ffmpeg'],
            'separator': ':',
            'output_name': 'GMClip'
        }

def main():
    platform_info = get_platform_info()
    
    # Prepare ffmpeg files
    ffmpeg_files = []
    for file in platform_info['ffmpeg_files']:
        src = os.path.join(platform_info['ffmpeg_path'], file)
        if os.path.exists(src):
            ffmpeg_files.append((src, '.'))
            print(f"Found {src} , adding to the build")

    # Build with PyInstaller
    PyInstaller.__main__.run([
        'block_editor/__main__.py',
        '--name=GMClip',
        '--onefile',
        '--windowed',
        '--add-data=' + platform_info['separator'].join(['label_manager.py', '.']),
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtMultimedia',
        '--hidden-import=PySide6.QtMultimediaWidgets',
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=pydub',
        *[f'--add-binary={src}{platform_info["separator"]}{dst}' for src, dst in ffmpeg_files],
        '--clean',
        '--noconfirm'
    ])

    # Move the built executable to dist directory with platform-specific name
    if os.path.exists('dist'):
        src = os.path.join('dist', 'GMClip' + ('.exe' if sys.platform == 'win32' else ''))
        dst_dir = os.path.join('dist', sys.platform)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, platform_info['output_name'])
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"Successfully built {dst}")

if __name__ == "__main__":
    main()
